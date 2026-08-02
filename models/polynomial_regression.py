from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures

from utils.ml_harness import fit_return_based_model

DEGREE = 2


def perform_polynomial_regression(data, test_frac: float = 0.2):
    estimator = Pipeline([
        ("poly", PolynomialFeatures(degree=DEGREE, include_bias=False)),
        ("lr", LinearRegression()),
    ])
    return fit_return_based_model(estimator, data, test_frac)
