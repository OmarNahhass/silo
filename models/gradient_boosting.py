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
        n_jobs=-1,
    )
    return fit_return_based_model(estimator, data, test_frac)
