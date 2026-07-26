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
from utils.plotting import plot_price_history, plot_prediction, PLOTLY_CONFIG
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS

st.set_page_config(page_title="CryptoCast", page_icon="📈", layout="wide")

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stMetric"] {
    background-color: #252836;
    border: 1px solid hsla(236, 7%, 54%, 0.24);
    border-radius: 10px;
    padding: 16px 16px 12px 16px;
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


def render_ticker_and_run_controls(asset_type: str):
    """Sidebar ticker/period/run controls for one fixed asset type (Stock or Crypto page).

    st.navigation resets widget-keyed session_state when switching pages, even when the
    same widget key is reused on the destination page -- so relying on `key=` alone would
    make the sidebar visually snap back to its defaults every time you navigate, even
    though the underlying forecast (a plain, non-widget session_state entry) is still
    intact. Seeding each widget's initial value/index from the last *submitted* settings
    works around that: it only resets on navigation, not on every rerun, since Streamlit
    still prefers live in-page widget interaction over the seeded default.
    """
    prior = st.session_state.get("forecast", {})
    same_asset = prior.get("asset_type") == asset_type

    with st.sidebar:
        st.header(f"{asset_type} Settings")

        curated = STOCK_TICKERS if asset_type == "Stock" else CRYPTO_TICKERS
        prior_ticker = prior.get("ticker", "") if same_asset else ""
        options = ([prior_ticker] if prior_ticker and prior_ticker not in curated else []) + curated + ["Custom ticker..."]
        default_ticker = prior_ticker if prior_ticker in options else options[0]
        selected = st.selectbox(
            "Search ticker symbol", options, index=options.index(default_ticker),
            key=f"{asset_type}_ticker_select",
        )
        if selected == "Custom ticker...":
            ticker = st.text_input(
                "Ticker symbol", placeholder="e.g. UBER" if asset_type == "Stock" else "e.g. PEPE",
                key=f"{asset_type}_custom_ticker",
            ).strip().upper()
        else:
            ticker = selected

        period_default = prior.get("period", PERIOD_OPTIONS[2]) if same_asset else PERIOD_OPTIONS[2]
        period = st.selectbox(
            "History length", PERIOD_OPTIONS, index=PERIOD_OPTIONS.index(period_default), key="period",
        )
        run = st.button("Run Forecast", type="primary", use_container_width=True, key=f"{asset_type}_run_button")

    # st.button only returns True on the exact rerun it was clicked on -- navigating to a
    # different page, or any other widget interaction, triggers its own rerun where `run`
    # goes back to False. Cache the computed forecast in session_state so it survives
    # navigation instead of every page needing a fresh click of "Run Forecast".
    if not run:
        return

    if not ticker:
        st.error("Enter a ticker symbol first.")
        return

    try:
        with st.spinner(f"Fetching {ticker} data..."):
            data = fetch_data(ticker, asset_type=asset_type, period=period)
    except Exception as e:
        st.error(f"Couldn't fetch data for {ticker}: {e}")
        return

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
        "asset_type": asset_type,
        "period": period,
        "data": data,
        "close": close,
        "last_close": float(close.iloc[-1]),
        "results": results,
        "errors": errors,
    }


def render_dashboard_page():
    st.title("CryptoCast")
    st.caption("Forecasting stocks and crypto with classical statistics and machine learning.")

    if "forecast" not in st.session_state:
        st.info("Pick **Stock** or **Crypto** in the sidebar to search a ticker and run a forecast.")
        return

    state = st.session_state.forecast
    results, last_close = state["results"], state["last_close"]

    st.subheader(f"{state['ticker']} — {len(state['data'])} trading days")
    st.plotly_chart(
        plot_price_history(state["data"], state["ticker"]),
        config=PLOTLY_CONFIG, use_container_width=True,
    )

    with st.expander("Raw data"):
        st.dataframe(state["data"], use_container_width=True)

    st.subheader("Forecasts")
    st.caption(f"Go to **{state['asset_type']}** in the sidebar to pick one model's full chart and math.")
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


def make_asset_page(asset_type: str):
    """Build the Stock or Crypto page: ticker/run controls, then a model dropdown."""

    def render():
        render_ticker_and_run_controls(asset_type)
        st.title(f"{asset_type} Forecasts")

        state = st.session_state.get("forecast")
        if not state or state.get("asset_type") != asset_type:
            st.info(f"Search a {asset_type.lower()} ticker in the sidebar, then click **Run Forecast**.")
            return

        results, errors = state["results"], state["errors"]

        st.subheader(f"{state['ticker']} — {len(state['data'])} trading days")
        st.plotly_chart(
            plot_price_history(state["data"], state["ticker"]),
            config=PLOTLY_CONFIG, use_container_width=True,
        )
        with st.expander("Raw data"):
            st.dataframe(state["data"], use_container_width=True)

        st.subheader("Select a forecasting model")
        sort_by_accuracy = st.checkbox(
            "Sort by most accurate (lowest holdout RMSE first)", key=f"{asset_type}_sort_toggle",
        )

        def rmse_of(spec):
            result = results.get(spec["key"])
            return result["rmse"] if result and result["rmse"] == result["rmse"] else float("inf")

        ordered = sorted(MODELS, key=rmse_of) if sort_by_accuracy else MODELS

        def label(spec):
            result = results.get(spec["key"])
            if result is None:
                return f"{spec['name']} (failed)"
            if result["rmse"] == result["rmse"]:
                return f"{spec['name']} — RMSE ${result['rmse']:.2f}"
            return spec["name"]

        selected_key = st.selectbox(
            "Forecasting model", [spec["key"] for spec in ordered],
            format_func=lambda key: label(next(s for s in MODELS if s["key"] == key)),
            key=f"{asset_type}_model_select",
        )
        spec = next(s for s in MODELS if s["key"] == selected_key)

        if spec["key"] not in results:
            st.error(f"{spec['name']} failed to run: {errors.get(spec['key'])}")
            return

        result = results[spec["key"]]
        st.caption(spec["category"])
        render_metric_tile(st, spec, result, state["last_close"])
        st.plotly_chart(
            plot_prediction(state["close"], result["fitted"], result["prediction"], spec["name"]),
            config=PLOTLY_CONFIG, use_container_width=True,
        )
        st.markdown("##### How it works")
        spec["math"]()
        st.markdown(spec["note"])

    render.__name__ = f"render_{asset_type.lower()}_page"
    return render


def run_app():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    pages = [
        st.Page(render_dashboard_page, title="Overview", icon="🏠", default=True),
        st.Page(make_asset_page("Stock"), title="Stock", icon="📈"),
        st.Page(make_asset_page("Crypto"), title="Crypto", icon="🪙"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    run_app()
