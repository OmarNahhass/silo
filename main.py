import warnings
warnings.filterwarnings("ignore")

import streamlit as st

from data_fetcher import fetch_data, PERIOD_OPTIONS
from models.linear_regression import perform_linear_regression
from models.arima import perform_arima_prediction, ORDER as ARIMA_ORDER
from models.ets import perform_ets_prediction
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

    cols = st.columns(len(MODELS))
    results = {}
    for col, spec in zip(cols, MODELS):
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
