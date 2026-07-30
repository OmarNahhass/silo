from xgboost import XGBRegressor

from utils.ml_harness import fit_return_based_model

N_ESTIMATORS = 300
MAX_DEPTH = 3
LEARNING_RATE = 0.05


def perform_gradient_boosting_prediction(data, test_frac: float = 0.2):
    """Gradient-boosted trees: each new tree fit to the residual errors of the ensemble so far."""
    estimator = XGBRegressor(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        learning_rate=LEARNING_RATE,
        random_state=42,
        # n_jobs=1, not -1: the API already runs all 10 models concurrently in a thread
        # pool, so letting this also grab every core would oversubscribe the CPU and
        # fight the other 9 models for the same cores instead of actually parallelizing.
        n_jobs=1,
    )
    return fit_return_based_model(estimator, data, test_frac)
