import math
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analysis.stats import (
    mean,
    median,
    variance,
    standard_deviation,
    covariance,
    correlation,
)

def test_mean_returns_correct_average():
    assert mean([1, 2, 3, 4, 5]) == 3.0
    assert mean([10, 20]) == 15.0
    assert mean([2.5, 3.5]) == 3.0


def test_mean_raises_on_empty_list():
    with pytest.raises(ValueError):
        mean([])


def test_median_odd_list():
    assert median([3, 1, 2]) == 2


def test_median_even_list():
    assert median([4, 1, 2, 3]) == 2.5

def test_median_raises_on_empty_list():
    with pytest.raises(ValueError):
        median([])

def test_variance_returns_expected_value():
    # même cas que celui du prof
    result = variance([2, 4, 4, 4, 5, 5, 7, 9])
    assert abs(result - 4.0) < 1e-9

def test_variance_raises_on_empty_list():
    with pytest.raises(ValueError):
        variance([])

def test_standard_deviation_returns_expected_value():
    result = standard_deviation([2, 4, 4, 4, 5, 5, 7, 9])
    assert abs(result - 2.0) < 1e-9

def test_standard_deviation_raises_on_empty_list():
    with pytest.raises(ValueError):
        standard_deviation([])

def test_covariance_returns_positive_value_for_related_series():
    xs = [1, 2, 3]
    ys = [2, 4, 6]
    assert abs(covariance(xs, ys) - (4 / 3)) < 1e-9

def test_covariance_raises_if_lists_are_empty():
    with pytest.raises(ValueError):
        covariance([], [1, 2, 3])

    with pytest.raises(ValueError):
        covariance([1, 2, 3], [])

def test_covariance_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        covariance([1, 2], [1, 2, 3])

def test_correlation_identical_series_is_one():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(correlation(xs, xs) - 1.0) < 1e-9

def test_correlation_opposite_series_is_minus_one():
    xs = [1, 2, 3, 4]
    ys = [4, 3, 2, 1]
    assert abs(correlation(xs, ys) + 1.0) < 1e-9

def test_correlation_returns_zero_if_one_series_has_zero_std():
    xs = [3, 3, 3]
    ys = [1, 2, 3]
    assert correlation(xs, ys) == 0

def test_correlation_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        correlation([1, 2], [1])