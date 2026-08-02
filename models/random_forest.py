from sklearn.ensemble import RandomForestRegressor

from utils.ml_harness import fit_return_based_model

N_ESTIMATORS = 300
MAX_DEPTH = 5


def perform_random_forest_prediction(data, test_frac: float = 0.2):
    estimator = RandomForestRegressor(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=42,
        n_jobs=1,
    )
    return fit_return_based_model(estimator, data, test_frac)
