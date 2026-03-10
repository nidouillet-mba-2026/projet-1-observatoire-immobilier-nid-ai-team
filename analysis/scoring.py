from analysis.regression import predict

def expected_price(alpha: float, beta: float, surface: float) -> float:
    """Estime le prix attendu d'un bien à partir de sa surface."""
    return predict(alpha, beta, surface)

def opportunity_score(expected_price: float, listed_price: float) -> float:
    """
    Calcule un score d'opportunité
    Score > 0 : bien moins cher que prévu
    Score < 0 : bien plus cher que prévu
    """
    if listed_price <= 0:
        raise ValueError("Le prix affiché doit être positif")

    return (expected_price - listed_price) / listed_price

def classify_property(expected_price_value: float, listed_price: float, threshold: float = 0.10) -> str:
    """Classe un bien en opportunité, prix marché ou surévalué"""
    score = opportunity_score(expected_price_value, listed_price)

    if score > threshold:
        return "Opportunité"
    elif score < -threshold:
        return "Surévalué"
    else:
        return "Prix marché"