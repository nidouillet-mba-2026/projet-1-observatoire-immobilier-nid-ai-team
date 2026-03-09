import math

def distance(a: list[float], b: list[float]) -> float:
    """Calcule la distance euclidienne entre deux vecteurs."""
    if len(a) != len(b):
        raise ValueError("Les vecteurs doivent avoir la même longueur")

    total = 0
    for i in range(len(a)):
        total += (a[i] - b[i]) ** 2

    return math.sqrt(total)

def knn_similar(target: list[float], properties: list[list[float]], k: int = 5) -> list[tuple[float, list[float]]]:
    """
    Retourne les k biens les plus similaires au bien cible.
    Chaque résultat est un tuple (distance, bien).
    """
    distances = []

    for prop in properties:
        d = distance(target, prop)
        distances.append((d, prop))

    distances.sort(key=lambda x: x[0])
    return distances[:k]