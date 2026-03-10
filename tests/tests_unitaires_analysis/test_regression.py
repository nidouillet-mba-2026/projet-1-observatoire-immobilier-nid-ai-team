import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analysis.regression import (
    predict,
    error,
    sum_of_sqerrors,
    least_squares_fit,
    r_squared,
)


def test_predict_returns_linear_prediction():
    assert predict(1.0, 2.0, 3.0) == 7.0


def test_error_returns_difference_between_true_and_predicted():
    # y = 10, prediction = 7
    assert error(1.0, 2.0, 3.0, 10.0) == 3.0


def test_sum_of_sqerrors_returns_zero_for_perfect_fit():
    x = [1, 2, 3]
    y = [3, 5, 7]
    assert sum_of_sqerrors(1.0, 2.0, x, y) == 0.0


def test_sum_of_sqerrors_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        sum_of_sqerrors(1.0, 2.0, [1, 2], [3])


def test_least_squares_fit_finds_expected_alpha_and_beta():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]

    alpha, beta = least_squares_fit(x, y)

    assert abs(alpha - 1.0) < 1e-9
    assert abs(beta - 2.0) < 1e-9


def test_least_squares_fit_raises_if_inputs_empty():
    with pytest.raises(ValueError):
        least_squares_fit([], [])


def test_least_squares_fit_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        least_squares_fit([1, 2], [3])


def test_least_squares_fit_raises_if_variance_of_x_is_zero():
    with pytest.raises(ValueError):
        least_squares_fit([2, 2, 2], [1, 2, 3])


def test_r_squared_is_one_for_perfect_fit():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]

    alpha, beta = least_squares_fit(x, y)
    result = r_squared(alpha, beta, x, y)

    assert abs(result - 1.0) < 1e-9


def test_r_squared_returns_one_if_y_is_constant_and_fit_is_perfect():
    x = [1, 2, 3]
    y = [5, 5, 5]
    result = r_squared(5.0, 0.0, x, y)
    assert result == 1.0


def test_r_squared_raises_if_lengths_differ():
    with pytest.raises(ValueError):
        r_squared(1.0, 2.0, [1, 2], [3])