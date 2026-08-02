from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils.ml_harness import fit_return_based_model

N_NEIGHBORS = 8


def perform_knn_prediction(data, test_frac: float = 0.2):
    estimator = Pipeline([
        ("scale", StandardScaler()),
        ("knn", KNeighborsRegressor(n_neighbors=N_NEIGHBORS)),
    ])
    return fit_return_based_model(estimator, data, test_frac)
