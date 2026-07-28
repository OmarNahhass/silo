import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import streamlit as st

from data_fetcher import fetch_data, PERIOD_OPTIONS
from model_registry import MODELS, STATISTICAL, MACHINE_LEARNING
from utils.plotting import plot_price_history, plot_prediction, PLOTLY_CONFIG
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS

st.set_page_config(page_title="CryptoCast", layout="wide")

# Font stack and text sizing pulled from fightledger.vercel.app (system-ui stack, bold
# 16px/-0.3px brand text, 22px/-0.4px h1, 14px/600 nav links, 13px muted captions).
GLOBAL_CSS = """
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
h1 {
    font-size: 22px !important;
    font-weight: 700 !important;
    letter-spacing: -0.4px !important;
}
h2, h3 {
    font-size: 17px !important;
    font-weight: 700 !important;
}
[data-testid="stSidebarNavLink"] p {
    font-size: 14px;
    font-weight: 600;
}
[data-testid="stMetric"] {
    background-color: #262626;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 16px 16px 12px 16px;
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
}
</style>
"""

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
    leaderboard.insert(0, "Rank", leaderboard.index)
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
        st.latex(spec["math"])
        st.markdown(spec["note"])

    render.__name__ = f"render_{asset_type.lower()}_page"
    return render


def run_app():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.logo("assets/logo.svg", size="large")

    pages = [
        st.Page(render_dashboard_page, title="Overview", icon=":material/dashboard:", default=True),
        st.Page(make_asset_page("Stock"), title="Stock", icon=":material/show_chart:"),
        st.Page(make_asset_page("Crypto"), title="Crypto", icon=":material/currency_bitcoin:"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    run_app()
