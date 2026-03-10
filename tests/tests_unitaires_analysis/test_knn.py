import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analysis.knn import distance, knn_similar


def test_distance_returns_zero_for_identical_vectors():
    assert distance([1, 2], [1, 2]) == 0.0


def test_distance_returns_euclidean_distance():
    # sqrt((3-0)^2 + (4-0)^2) = 5
    assert distance([0, 0], [3, 4]) == 5.0


def test_distance_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        distance([1, 2], [1])


def test_knn_similar_returns_k_closest_properties():
    target = [0, 0]
    properties = [
        [10, 10],  # distance élevée
        [1, 1],    # proche
        [2, 2],    # proche
        [0, 1],    # très proche
    ]

    result = knn_similar(target, properties, k=2)

    assert len(result) == 2
    assert result[0][1] == [0, 1]
    assert result[1][1] == [1, 1]


def test_knn_similar_returns_all_if_k_exceeds_length():
    target = [0, 0]
    properties = [[1, 1], [2, 2]]

    result = knn_similar(target, properties, k=5)

    assert len(result) == 2


def test_knn_similar_sorts_by_distance():
    target = [0, 0]
    properties = [[3, 4], [1, 1], [2, 2]]

    result = knn_similar(target, properties, k=3)
    distances = [item[0] for item in result]

    assert distances == sorted(distances)