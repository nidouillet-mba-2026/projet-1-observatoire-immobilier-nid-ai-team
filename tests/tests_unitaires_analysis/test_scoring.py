import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analysis.scoring import (
    expected_price,
    opportunity_score,
    classify_property,
)


def test_expected_price_uses_linear_prediction():
    # expected = alpha + beta * surface = 10000 + 2000 * 50
    assert expected_price(10000, 2000, 50) == 110000


def test_opportunity_score_positive_when_listed_below_expected():
    result = opportunity_score(120000, 100000)
    assert abs(result - 0.2) < 1e-9


def test_opportunity_score_negative_when_listed_above_expected():
    result = opportunity_score(100000, 120000)
    assert result < 0


def test_opportunity_score_zero_when_same_price():
    assert opportunity_score(100000, 100000) == 0.0

def test_opportunity_score_raises_if_listed_price_not_positive():
    with pytest.raises(ValueError):
        opportunity_score(100000, 0)

    with pytest.raises(ValueError):
        opportunity_score(100000, -10)


def test_classify_property_opportunity():
    assert classify_property(120000, 100000) == "Opportunité"


def test_classify_property_overpriced():
    assert classify_property(100000, 120000) == "Surévalué"


def test_classify_property_market_price():
    assert classify_property(105000, 100000, threshold=0.10) == "Prix marché"