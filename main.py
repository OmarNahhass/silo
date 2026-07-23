import warnings
warnings.filterwarnings("ignore")

import streamlit as st

from data_fetcher import fetch_data, PERIOD_OPTIONS
from models.linear_regression import perform_linear_regression
from models.arima import perform_arima_prediction, ORDER as ARIMA_ORDER
from models.ets import perform_ets_prediction
from models.polynomial_regression import perform_polynomial_regression, DEGREE as POLY_DEGREE
from models.knn import perform_knn_prediction, N_NEIGHBORS
from models.random_forest import perform_random_forest_prediction
from models.svr import perform_svr_prediction, EPSILON as SVR_EPSILON
from utils.plotting import plot_price_history, plot_prediction

st.set_page_config(page_title="CryptoCast", page_icon="📈", layout="wide")

MODELS = [
    {
        "key": "lr",
        "name": "Linear Regression",
        "run": perform_linear_regression,
        "math": lambda: st.latex(r"\text{Close}_{t+1} = \beta_0 + \beta_1 \cdot \text{Close}_t + \varepsilon_t"),
        "note": "Fits a straight line between today's close and tomorrow's close, "
                "choosing $\\beta_0, \\beta_1$ to minimize the sum of squared errors (OLS).",
    },
    {
        "key": "arima",
        "name": "ARIMA",
        "run": perform_arima_prediction,
        "math": lambda: st.latex(
            r"\left(1 - \sum_{i=1}^{5}\phi_i L^i\right)(1-L)\,y_t = \varepsilon_t"
        ),
        "note": f"ARIMA{ARIMA_ORDER}: models the day-to-day *differenced* price as a linear "
                "combination of its own past 5 values (autoregression), so it captures momentum "
                "and mean-reverting behavior that a flat line can't.",
    },
    {
        "key": "ets",
        "name": "ETS (Holt's Linear Trend)",
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
        "key": "poly",
        "name": "Polynomial Regression",
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
        "key": "svr",
        "name": "Support Vector Regression",
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


def main():
    st.title("CryptoCast")
    st.caption("Forecasting stocks and crypto with classical statistics and machine learning.")

    with st.sidebar:
        st.header("Settings")
        asset_type = st.radio("Asset type", ["Stock", "Crypto"], horizontal=True)
        placeholder = "AAPL" if asset_type == "Stock" else "BTC"
        ticker = st.text_input("Ticker symbol", placeholder=placeholder).strip().upper()
        period = st.selectbox("History length", PERIOD_OPTIONS, index=2)
        run = st.button("Run Forecast", type="primary", use_container_width=True)

    if not run:
        st.info("Choose an asset type and ticker in the sidebar, then click **Run Forecast**.")
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

    st.subheader(f"{ticker} — {len(data)} trading days")
    st.plotly_chart(plot_price_history(data, ticker), use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(data, use_container_width=True)

    st.subheader("Forecasts")
    close = data["Close"].dropna()
    last_close = float(close.iloc[-1])

    results = {}
    row_size = 4
    for row_start in range(0, len(MODELS), row_size):
        row_specs = MODELS[row_start:row_start + row_size]
        cols = st.columns(row_size)
        for col, spec in zip(cols, row_specs):
            try:
                result = spec["run"](data)
                results[spec["key"]] = result
                delta = result["prediction"] - last_close
                col.metric(
                    spec["name"],
                    f"${result['prediction']:.2f}",
                    f"{delta:+.2f} ({delta / last_close:+.2%})",
                )
                rmse_val = result["rmse"]
                col.caption(f"Holdout RMSE: ${rmse_val:.2f}" if rmse_val == rmse_val else "Holdout RMSE: n/a")
            except Exception as e:
                col.error(f"{spec['name']} failed: {e}")

    for spec in MODELS:
        if spec["key"] not in results:
            continue
        result = results[spec["key"]]
        st.markdown(f"#### {spec['name']}")
        st.plotly_chart(
            plot_prediction(close, result["fitted"], result["prediction"], spec["name"]),
            use_container_width=True,
        )
        with st.expander(f"How {spec['name']} works"):
            spec["math"]()
            st.markdown(spec["note"])


if __name__ == "__main__":
    main()
