"""Simple PAP scraper for Toulon listings.

This module collects listing links from PAP search pages, extracts key fields
from detail pages, and exports a CSV used by the Streamlit app.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    import cloudscraper
except ImportError:  # pragma: no cover - optional runtime dependency
    cloudscraper = None


PAP_BASE = "https://www.pap.fr"
DEFAULT_CITY_SLUG = "toulon-83-g43611"
CSV_COLUMNS = [
    "source",
    "titre",
    "prix_eur",
    "surface_m2",
    "quartier",
    "type_bien",
    "description",
    "url",
    "date_scrape",
]


@dataclass
class ScrapeConfig:
    budget_max: int = 500_000
    limit: int = 100
    max_pages: int = 12
    city_slug: str = DEFAULT_CITY_SLUG
    search_url: str = ""
    city_keywords: tuple[str, ...] = ("toulon", "83000", "83100", "83200")
    timeout_s: int = 20


def _session() -> requests.Session:
    if cloudscraper is not None:
        s = cloudscraper.create_scraper()
    else:
        s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
    )
    return s


def _search_url(city_slug: str, budget_max: int, page: int) -> str:
    base = f"{PAP_BASE}/annonce/vente-immobiliere-{city_slug}-jusqu-a-{budget_max}-euros"
    if page <= 1:
        return base
    return f"{base}?page={page}"


def _search_url_from_config(config: ScrapeConfig, page: int) -> str:
    if config.search_url:
        if page <= 1:
            return config.search_url
        separator = "&" if "?" in config.search_url else "?"
        return f"{config.search_url}{separator}page={page}"
    return _search_url(config.city_slug, config.budget_max, page)


def _extract_listing_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/annonces/" not in href:
            continue
        if any(skip in href for skip in ["#", "mailto:", "javascript:"]):
            continue
        full = urljoin(PAP_BASE, href.split("?")[0])
        if full.startswith(PAP_BASE):
            urls.add(full)
    return sorted(urls)


def _extract_listing_rows_from_search(html: str, budget_max: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/annonces/" not in href:
            continue

        url = urljoin(PAP_BASE, href.split("?")[0])
        if url in seen:
            continue
        seen.add(url)

        title = _safe_text(a.get_text(" ", strip=True))
        container = a.find_parent(["article", "li", "div"]) or a
        container_text = _safe_text(container.get_text(" ", strip=True))

        price = _price_from_text(container_text)
        surface = _surface_from_text(container_text)

        if not title:
            star_match = re.search(r"\*\*(.*?)\*\*", container_text)
            if star_match:
                title = _safe_text(star_match.group(1))
        if not title:
            title = _safe_text(container_text[:120])

        if price is None or price <= 0 or price > budget_max:
            continue
        if surface is None or surface <= 0:
            continue

        rows.append(
            {
                "source": "PAP",
                "titre": title,
                "prix_eur": price,
                "surface_m2": surface,
                "quartier": "",
                "type_bien": _type_from_title(title),
                "description": "",
                "url": url,
                "date_scrape": datetime.now(timezone.utc).isoformat(),
            }
        )

    return rows


def _city_match(item: dict, keywords: tuple[str, ...]) -> bool:
    if not keywords:
        return True
    haystack = " ".join(
        [
            str(item.get("titre", "")),
            str(item.get("description", "")),
            str(item.get("url", "")),
        ]
    ).lower()
    return any(k.lower() in haystack for k in keywords)


def _safe_text(value: str | None) -> str:
    return value.strip() if value else ""


def _price_from_text(text: str) -> float | None:
    m = re.search(r"(\d[\d\s\.,]{2,})\s*€", text.replace("\xa0", " "))
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    return float(digits) if digits else None


def _surface_from_text(text: str) -> float | None:
    m = re.search(r"(\d+[\.,]?\d*)\s*m²", text.lower())
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _type_from_title(title: str) -> str:
    lower = title.lower()
    if "appartement" in lower:
        return "Appartement"
    if "maison" in lower:
        return "Maison"
    return "Autre"


def _extract_jsonld_objects(soup: BeautifulSoup) -> Iterable[dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield item
        elif isinstance(payload, dict):
            yield payload


def _extract_from_jsonld(objects: Iterable[dict]) -> dict:
    out: dict[str, str | float | None] = {
        "titre": "",
        "description": "",
        "prix_eur": None,
        "surface_m2": None,
        "quartier": "",
    }
    for obj in objects:
        if not out["titre"]:
            out["titre"] = _safe_text(str(obj.get("name", "")))
        if not out["description"]:
            out["description"] = _safe_text(str(obj.get("description", "")))

        offers = obj.get("offers")
        if isinstance(offers, dict) and out["prix_eur"] is None:
            price = offers.get("price")
            if isinstance(price, (int, float, str)):
                try:
                    out["prix_eur"] = float(str(price).replace(",", "."))
                except ValueError:
                    pass

        floor = obj.get("floorSize")
        if isinstance(floor, dict) and out["surface_m2"] is None:
            value = floor.get("value")
            if isinstance(value, (int, float, str)):
                try:
                    out["surface_m2"] = float(str(value).replace(",", "."))
                except ValueError:
                    pass

        address = obj.get("address")
        if isinstance(address, dict) and not out["quartier"]:
            out["quartier"] = _safe_text(str(address.get("addressLocality", "")))

    return out


def _parse_detail_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    title = _safe_text(h1.get_text(" ", strip=True) if h1 else "")
    description = ""

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        description = _safe_text(og_desc["content"])

    text_blob = soup.get_text(" ", strip=True)
    price = _price_from_text(text_blob)
    surface = _surface_from_text(text_blob)

    jsonld_data = _extract_from_jsonld(_extract_jsonld_objects(soup))
    if not title:
        title = str(jsonld_data.get("titre") or "")
    if not description:
        description = str(jsonld_data.get("description") or "")
    if price is None:
        price = jsonld_data.get("prix_eur")  # type: ignore[assignment]
    if surface is None:
        surface = jsonld_data.get("surface_m2")  # type: ignore[assignment]

    quartier = str(jsonld_data.get("quartier") or "")
    type_bien = _type_from_title(title)

    return {
        "source": "PAP",
        "titre": title,
        "prix_eur": price,
        "surface_m2": surface,
        "quartier": quartier,
        "type_bien": type_bien,
        "description": description,
        "url": url,
        "date_scrape": datetime.now(timezone.utc).isoformat(),
    }


def scrape_pap_annonces(config: ScrapeConfig, output_path: Path | str = "data/annonces.csv") -> pd.DataFrame:
    output = Path(output_path)
    s = _session()
    rows: list[dict] = []

    for page in range(1, config.max_pages + 1):
        search_url = _search_url_from_config(config, page)
        try:
            resp = s.get(search_url, timeout=config.timeout_s)
        except requests.RequestException:
            continue

        if resp.status_code >= 400:
            continue

        page_rows = _extract_listing_rows_from_search(resp.text, config.budget_max)
        rows.extend(page_rows)
        if len(rows) >= config.limit:
            break

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=CSV_COLUMNS)
    else:
        df = df.drop_duplicates(subset=["url"], keep="first")
        df = df[df.apply(lambda row: _city_match(row.to_dict(), config.city_keywords), axis=1)]
        df = df.head(config.limit)
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[CSV_COLUMNS]

    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df


if __name__ == "__main__":
    cfg = ScrapeConfig()
    result = scrape_pap_annonces(cfg)
    print(f"Saved {len(result)} annonces to data/annonces.csv")
