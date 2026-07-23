from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from utils.ml_harness import fit_return_based_model

EPSILON = 0.002  # tolerance band, in log-return units


def perform_svr_prediction(data, test_frac: float = 0.2):
    """Epsilon-insensitive SVR with an RBF kernel over the technical-indicator features."""
    estimator = Pipeline([
        ("scale", StandardScaler()),
        ("svr", SVR(kernel="rbf", C=1.0, epsilon=EPSILON)),
    ])
    return fit_return_based_model(estimator, data, test_frac)
