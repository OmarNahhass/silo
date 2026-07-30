"""Single source of truth for the 10 forecasting models: which function runs each one,
what category it belongs to, and the math/explanation shown alongside its results.
Framework-agnostic (no Streamlit/FastAPI imports) so both main.py (Streamlit) and
api.py (FastAPI backend) can import MODELS directly without duplicating this content.
"""

from models.linear_regression import perform_linear_regression
from models.arima import perform_arima_prediction, ORDER as ARIMA_ORDER
from models.sarima import perform_sarima_prediction, ORDER as SARIMA_ORDER, SEASONAL_ORDER
from models.ets import perform_ets_prediction
from models.prophet_style import (
    perform_prophet_style_prediction,
    N_CHANGEPOINTS,
    FOURIER_ORDER,
)
from models.polynomial_regression import perform_polynomial_regression, DEGREE as POLY_DEGREE
from models.knn import perform_knn_prediction, N_NEIGHBORS
from models.random_forest import perform_random_forest_prediction
from models.gradient_boosting import perform_gradient_boosting_prediction
from models.svr import perform_svr_prediction, EPSILON as SVR_EPSILON

STATISTICAL = "Statistical"
MACHINE_LEARNING = "Machine Learning"
ENSEMBLE = "Ensemble"

MODELS = [
    {
        "key": "lr",
        "name": "Linear Regression",
        "category": STATISTICAL,
        "run": perform_linear_regression,
        "math": r"\text{Close}_{t+1} = \beta_0 + \beta_1 \cdot \text{Close}_t + \varepsilon_t",
        "note": "Fits a straight line between today's close and tomorrow's close, "
                "choosing $\\beta_0, \\beta_1$ to minimize the sum of squared errors (OLS).",
    },
    {
        "key": "arima",
        "name": "ARIMA",
        "category": STATISTICAL,
        "run": perform_arima_prediction,
        "math": r"\left(1 - \sum_{i=1}^{5}\phi_i L^i\right)(1-L)\,y_t = \varepsilon_t",
        "note": f"ARIMA{ARIMA_ORDER}: models the day-to-day *differenced* price as a linear "
                "combination of its own past 5 values (autoregression), so it captures momentum "
                "and mean-reverting behavior that a flat line can't.",
    },
    {
        "key": "sarima",
        "name": "SARIMA",
        "category": STATISTICAL,
        "run": perform_sarima_prediction,
        "math": r"\phi(L)\,\Phi(L^7)\,(1-L)(1-L^7)\,y_t = \theta(L)\,\Theta(L^7)\,\varepsilon_t",
        "note": f"SARIMA{SARIMA_ORDER}x{SEASONAL_ORDER}: ARIMA plus a second autoregressive/moving-"
                "average block applied 7 days apart, on top of a *weekly* seasonal differencing "
                "term. Meant to capture a repeating weekly pattern in the price on top of the "
                "ordinary day-to-day momentum ARIMA already models.",
    },
    {
        "key": "ets",
        "name": "ETS (Holt's Linear Trend)",
        "category": STATISTICAL,
        "run": perform_ets_prediction,
        "math": r"\begin{aligned} l_t &= \alpha y_t + (1-\alpha)(l_{t-1}+b_{t-1}) \\ "
                r"b_t &= \beta (l_t - l_{t-1}) + (1-\beta) b_{t-1} \\ "
                r"\hat{y}_{t+h} &= l_t + h\, b_t \end{aligned}",
        "note": "Exponentially smooths a *level* and a *trend* component separately, then "
                "extrapolates the trend forward. Weights recent observations more heavily.",
    },
    {
        "key": "prophet",
        "name": "Prophet-style Decomposition",
        "category": STATISTICAL,
        "run": perform_prophet_style_prediction,
        "math": (
            r"y(t) = \underbrace{k\,t + m + \textstyle\sum_{j=1}^{"
            + str(N_CHANGEPOINTS)
            + r"} \delta_j \max(0, t - s_j)}_{\text{piecewise-linear trend}} + "
            r"\underbrace{\textstyle\sum_{n=1}^{"
            + str(FOURIER_ORDER)
            + r"} \big(a_n \sin\tfrac{2\pi n t}{7} + b_n \cos\tfrac{2\pi n t}{7}\big)}"
            r"_{\text{weekly seasonality}}"
        ),
        "note": f"A hand-built version of Facebook Prophet's model: a trend line allowed to bend "
                f"at {N_CHANGEPOINTS} fixed changepoints $s_j$, plus a weekly cycle written as a "
                f"{FOURIER_ORDER}-harmonic Fourier series, fit *together* in one linear regression "
                "(a piecewise-linear function and a periodic function are both just linear "
                "combinations of basis functions — a line, some hinges, some sines and cosines). "
                "Real Prophet fits the same additive structure with Bayesian priors that damp "
                "down the changepoint slopes; this version is the plain, un-regularized least-"
                "squares fit, so it can overreact to a sharp trend change right before the split.",
    },
    {
        "key": "poly",
        "name": "Polynomial Regression",
        "category": MACHINE_LEARNING,
        "run": perform_polynomial_regression,
        "math": r"\hat{r}_{t+1} = \beta_0 + \sum_{j} \beta_j x_j + \sum_{j \le k} \beta_{jk}\, x_j x_k",
        "note": f"Degree-{POLY_DEGREE} polynomial regression over technical-indicator features "
                r"$x$ (moving-average ratios, RSI, MACD, volatility), predicting the next-day "
                r"*log return* $r_{t+1} = \ln(\text{Close}_{t+1}/\text{Close}_t)$ rather than price "
                "directly, since returns are far closer to stationary than raw price levels. "
                "Adding the quadratic/interaction terms lets it capture curvature that plain "
                "linear regression can't, e.g. RSI mattering more near its extremes.",
    },
    {
        "key": "knn",
        "name": "k-Nearest Neighbors",
        "category": MACHINE_LEARNING,
        "run": perform_knn_prediction,
        "math": r"\hat{r}_{t+1} = \frac{1}{k}\sum_{i \,\in\, N_k(x)} r_i, "
                r"\quad N_k(x) = \text{the } k \text{ days with smallest } \|x - x_i\|_2",
        "note": f"Finds the $k={N_NEIGHBORS}$ historical days whose standardized technical-indicator "
                "\"fingerprint\" is closest (Euclidean distance) to today's, and averages what "
                "the return actually was on those days. No trend is fit at all — it's pure "
                "pattern-matching against history.",
    },
    {
        "key": "rf",
        "name": "Random Forest",
        "category": MACHINE_LEARNING,
        "run": perform_random_forest_prediction,
        "math": r"\hat{r} = \frac{1}{B}\sum_{b=1}^{B} T_b(x), \quad "
                r"\text{splits chosen to maximize } \operatorname{Var}(S) - "
                r"\sum_{c \in \{L,R\}} \frac{|S_c|}{|S|}\operatorname{Var}(S_c)",
        "note": "An ensemble of decision trees, each trained on a bootstrap resample of the data "
                "and a random subset of features. Each tree repeatedly splits the feature space "
                "to minimize the variance of returns within each resulting group; averaging many "
                "such trees ($B$) smooths out the overfitting any single tree would have.",
    },
    {
        "key": "gbm",
        "name": "Gradient Boosting (XGBoost)",
        "category": MACHINE_LEARNING,
        "run": perform_gradient_boosting_prediction,
        "math": r"F_0(x) = \bar{r}, \quad F_m(x) = F_{m-1}(x) + \eta \, h_m(x), "
                r"\quad h_m \approx \arg\min_h \sum_i \left[-\frac{\partial \mathcal{L}(r_i, F_{m-1}(x_i))}{\partial F_{m-1}(x_i)} - h(x_i)\right]^2",
        "note": "Builds trees sequentially rather than independently (unlike Random Forest): each "
                "new tree $h_m$ is fit to approximate the *negative gradient* of the loss from the "
                "ensemble so far — effectively, each tree corrects the previous ensemble's "
                "residual errors, scaled down by a small learning rate $\\eta$ so no single tree "
                "dominates the final prediction.",
    },
    {
        "key": "svr",
        "name": "Support Vector Regression",
        "category": MACHINE_LEARNING,
        "run": perform_svr_prediction,
        "math": r"\min_{w,b} \tfrac{1}{2}\|w\|^2 + C\sum_i \max\!\big(0,\, |r_i - (w \cdot \phi(x_i) + b)| - \varepsilon\big)",
        "note": f"Fits a function that pays no penalty for errors smaller than "
                f"$\\varepsilon={SVR_EPSILON}$ (a tolerance tube around the prediction) and only "
                r"penalizes larger misses, linearly. An RBF kernel $\phi$ lets that tube bend "
                "nonlinearly through feature space instead of staying flat.",
    },
]

# Not part of MODELS -- computed dynamically from the other 10 models' own results
# (api.py) rather than run against raw price data, so it doesn't fit the MODELS
# run-function contract. Kept here anyway since it's still static display metadata,
# same as everything else in this file.
ENSEMBLE_META = {
    "key": "ensemble",
    "name": "Ensemble (Weighted Average)",
    "category": ENSEMBLE,
    "math": r"\hat{y}_{ensemble} = \sum_{i=1}^{n} w_i\, \hat{y}_i, \quad "
            r"w_i = \frac{1/\text{RMSE}_i^2}{\sum_{j=1}^{n} 1/\text{RMSE}_j^2}",
    "note": "Combines every model above into a single prediction, weighting each by the "
            "inverse of its squared typical error -- models that have actually been more "
            "reliable for this ticker get more say, less reliable ones get less. This is "
            "the classic inverse-variance combination: it's the weighting that minimizes "
            "the combined error *if* each model's mistakes are independent of the others'. "
            "That assumption is never perfectly true here, but it's close enough that "
            "averaging several independently-built models is one of the most consistently "
            "effective techniques in forecasting -- each model is wrong in a different way, "
            "so combining them cancels out some of each one's individual mistakes. In "
            "practice this usually makes the ensemble the single most accurate option "
            "available, including versus whichever individual model ranks #1 on its own.",
}
