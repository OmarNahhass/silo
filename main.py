import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import streamlit as st

from data_fetcher import fetch_data, PERIOD_OPTIONS
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
from utils.plotting import plot_price_history, plot_prediction

st.set_page_config(page_title="CryptoCast", page_icon="📈", layout="wide")

CARD_CSS = """
<style>
[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid rgba(11,11,11,0.10);
    border-radius: 10px;
    padding: 16px 16px 12px 16px;
    box-shadow: 0 1px 2px rgba(11,11,11,0.04);
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
}
</style>
"""

STATISTICAL = "Statistical"
MACHINE_LEARNING = "Machine Learning"

MODELS = [
    {
        "key": "lr",
        "name": "Linear Regression",
        "category": STATISTICAL,
        "run": perform_linear_regression,
        "math": lambda: st.latex(r"\text{Close}_{t+1} = \beta_0 + \beta_1 \cdot \text{Close}_t + \varepsilon_t"),
        "note": "Fits a straight line between today's close and tomorrow's close, "
                "choosing $\\beta_0, \\beta_1$ to minimize the sum of squared errors (OLS).",
    },
    {
        "key": "arima",
        "name": "ARIMA",
        "category": STATISTICAL,
        "run": perform_arima_prediction,
        "math": lambda: st.latex(
            r"\left(1 - \sum_{i=1}^{5}\phi_i L^i\right)(1-L)\,y_t = \varepsilon_t"
        ),
        "note": f"ARIMA{ARIMA_ORDER}: models the day-to-day *differenced* price as a linear "
                "combination of its own past 5 values (autoregression), so it captures momentum "
                "and mean-reverting behavior that a flat line can't.",
    },
    {
        "key": "sarima",
        "name": "SARIMA",
        "category": STATISTICAL,
        "run": perform_sarima_prediction,
        "math": lambda: st.latex(
            r"\phi(L)\,\Phi(L^7)\,(1-L)(1-L^7)\,y_t = \theta(L)\,\Theta(L^7)\,\varepsilon_t"
        ),
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
        "math": lambda: st.latex(
            r"\begin{aligned} l_t &= \alpha y_t + (1-\alpha)(l_{t-1}+b_{t-1}) \\ "
            r"b_t &= \beta (l_t - l_{t-1}) + (1-\beta) b_{t-1} \\ "
            r"\hat{y}_{t+h} &= l_t + h\, b_t \end{aligned}"
        ),
        "note": "Exponentially smooths a *level* and a *trend* component separately, then "
                "extrapolates the trend forward. Weights recent observations more heavily.",
    },
    {
        "key": "prophet",
        "name": "Prophet-style Decomposition",
        "category": STATISTICAL,
        "run": perform_prophet_style_prediction,
        "math": lambda: st.latex(
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
        "math": lambda: st.latex(
            r"\hat{r}_{t+1} = \beta_0 + \sum_{j} \beta_j x_j + \sum_{j \le k} \beta_{jk}\, x_j x_k"
        ),
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
        "math": lambda: st.latex(
            r"\hat{r}_{t+1} = \frac{1}{k}\sum_{i \,\in\, N_k(x)} r_i, "
            r"\quad N_k(x) = \text{the } k \text{ days with smallest } \|x - x_i\|_2"
        ),
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
        "math": lambda: st.latex(
            r"\hat{r} = \frac{1}{B}\sum_{b=1}^{B} T_b(x), \quad "
            r"\text{splits chosen to maximize } \operatorname{Var}(S) - "
            r"\sum_{c \in \{L,R\}} \frac{|S_c|}{|S|}\operatorname{Var}(S_c)"
        ),
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
        "math": lambda: st.latex(
            r"F_0(x) = \bar{r}, \quad F_m(x) = F_{m-1}(x) + \eta \, h_m(x), "
            r"\quad h_m \approx \arg\min_h \sum_i \left[-\frac{\partial \mathcal{L}(r_i, F_{m-1}(x_i))}{\partial F_{m-1}(x_i)} - h(x_i)\right]^2"
        ),
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
        "math": lambda: st.latex(
            r"\min_{w,b} \tfrac{1}{2}\|w\|^2 + C\sum_i \max\!\big(0,\, |r_i - (w \cdot \phi(x_i) + b)| - \varepsilon\big)"
        ),
        "note": f"Fits a function that pays no penalty for errors smaller than "
                f"$\\varepsilon={SVR_EPSILON}$ (a tolerance tube around the prediction) and only "
                r"penalizes larger misses, linearly. An RBF kernel $\phi$ lets that tube bend "
                "nonlinearly through feature space instead of staying flat.",
    },
]

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def render_metric_tile(col, spec, result, last_close):
    delta = result["prediction"] - last_close
    col.metric(
        spec["name"],
        f"${result['prediction']:.2f}",
        f"{delta:+.2f} ({delta / last_close:+.2%})",
    )
    rmse_val = result["rmse"]
    col.caption(f"Holdout RMSE: ${rmse_val:.2f}" if rmse_val == rmse_val else "Holdout RMSE: n/a")


def render_overview_tab(results, last_close):
    for category in (STATISTICAL, MACHINE_LEARNING):
        cat_specs = [spec for spec in MODELS if spec["category"] == category]
        st.markdown(f"##### {category} Models")
        cols = st.columns(len(cat_specs))
        for col, spec in zip(cols, cat_specs):
            if spec["key"] in results:
                render_metric_tile(col, spec, results[spec["key"]], last_close)
            else:
                col.error(f"{spec['name']} failed")

    st.markdown("#### Leaderboard (ranked by holdout RMSE — lower is better)")
    leaderboard = pd.DataFrame([
        {
            "Model": spec["name"],
            "Category": spec["category"],
            "Prediction": results[spec["key"]]["prediction"],
            "Holdout RMSE": results[spec["key"]]["rmse"],
        }
        for spec in MODELS if spec["key"] in results
    ]).sort_values("Holdout RMSE", na_position="last").reset_index(drop=True)
    leaderboard.index += 1
    leaderboard.insert(0, "Rank", [MEDALS.get(i, str(i)) for i in leaderboard.index])
    st.dataframe(
        leaderboard.style.format({"Prediction": "${:.2f}", "Holdout RMSE": "${:.2f}"}),
        use_container_width=True,
        hide_index=True,
    )


def render_model_explorer_tab(results, errors, close, last_close):
    selected_name = st.selectbox("Choose a model to inspect", [spec["name"] for spec in MODELS])
    spec = next(s for s in MODELS if s["name"] == selected_name)

    if spec["key"] not in results:
        st.error(f"{spec['name']} failed to run: {errors.get(spec['key'])}")
        return

    result = results[spec["key"]]
    st.caption(spec["category"])
    render_metric_tile(st, spec, result, last_close)
    st.plotly_chart(
        plot_prediction(close, result["fitted"], result["prediction"], spec["name"]),
        use_container_width=True,
    )
    st.markdown("##### How it works")
    spec["math"]()
    st.markdown(spec["note"])


def main():
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.title("CryptoCast")
    st.caption("Forecasting stocks and crypto with classical statistics and machine learning.")

    with st.sidebar:
        st.header("Settings")
        asset_type = st.radio("Asset type", ["Stock", "Crypto"], horizontal=True)
        placeholder = "AAPL" if asset_type == "Stock" else "BTC"
        ticker = st.text_input("Ticker symbol", placeholder=placeholder).strip().upper()
        period = st.selectbox("History length", PERIOD_OPTIONS, index=2)
        run = st.button("Run Forecast", type="primary", use_container_width=True)

    # st.button only returns True on the exact rerun it was clicked on -- any later widget
    # interaction (e.g. the Model Explorer dropdown below) triggers its own rerun where `run`
    # goes back to False. Cache the computed forecast in session_state so it survives those
    # reruns instead of the whole page collapsing back to the "not run yet" state.
    if run:
        if not ticker:
            st.error("Enter a ticker symbol first.")
        else:
            try:
                with st.spinner(f"Fetching {ticker} data..."):
                    data = fetch_data(ticker, asset_type=asset_type, period=period)
            except Exception as e:
                st.error(f"Couldn't fetch data for {ticker}: {e}")
                data = None

            if data is not None:
                close = data["Close"].dropna()
                results, errors = {}, {}
                with st.spinner("Running forecasts..."):
                    for spec in MODELS:
                        try:
                            results[spec["key"]] = spec["run"](data)
                        except Exception as e:
                            errors[spec["key"]] = str(e)
                st.session_state.forecast = {
                    "ticker": ticker,
                    "data": data,
                    "close": close,
                    "last_close": float(close.iloc[-1]),
                    "results": results,
                    "errors": errors,
                }

    if "forecast" not in st.session_state:
        st.info("Choose an asset type and ticker in the sidebar, then click **Run Forecast**.")
        return

    state = st.session_state.forecast
    st.subheader(f"{state['ticker']} — {len(state['data'])} trading days")
    st.plotly_chart(plot_price_history(state["data"], state["ticker"]), use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(state["data"], use_container_width=True)

    st.subheader("Forecasts")
    # st.tabs doesn't remember which tab was active across a rerun triggered by a widget
    # inside it (e.g. the Model Explorer dropdown below) -- it silently snaps back to the
    # first tab. st.radio's value is unambiguous after any rerun, so use that instead.
    view = st.radio("View", ["Overview", "Model Explorer"], horizontal=True, label_visibility="collapsed")
    if view == "Overview":
        render_overview_tab(state["results"], state["last_close"])
    else:
        render_model_explorer_tab(state["results"], state["errors"], state["close"], state["last_close"])


if __name__ == "__main__":
    main()
