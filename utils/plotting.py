import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Palette (dark-surface steps -- see dataviz skill reference palette; the app now runs a
# permanent dark theme, so these are the dark variants for contrast against a near-black surface)
BLUE = "#3987e5"      # historical series
ORANGE = "#d95926"    # model fit (in-sample)
VIOLET = "#9085e9"    # forecast callout
GOOD = "#0ca30c"      # up day
CRITICAL = "#e66767"  # down day
MUTED = "#898781"

# Pass to every st.plotly_chart(..., config=PLOTLY_CONFIG) call: zoom with the scroll
# wheel instead of the click-drag box-zoom tool (dragmode="pan" below makes click-drag
# pan instead), and drop the now-redundant zoom/select buttons from the mode bar.
PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["zoom2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "lasso2d", "select2d"],
}


def plot_price_history(df, ticker: str):
    """Candlestick price chart with a volume panel underneath (shared x-axis, no dual y-axis)."""
    up = df["Close"] >= df["Open"]
    vol_colors = [GOOD if u else CRITICAL for u in up]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25], vertical_spacing=0.04,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            increasing_line_color=GOOD, decreasing_line_color=CRITICAL,
            name=ticker,
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors, name="Volume", showlegend=False),
        row=2, col=1,
    )

    fig.update_layout(
        title=f"{ticker} Price History",
        xaxis_rangeslider_visible=False,
        dragmode="pan",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


def plot_prediction(close: "pd.Series", fitted: "pd.Series", predicted_value: float, model_name: str):
    """Historical close, in-sample model fit (dashed), and the next-step forecast (callout marker)."""
    next_date = close.index[-1] + (close.index[-1] - close.index[-2])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=close.index, y=close.values, mode="lines", name="Actual Close",
        line=dict(color=BLUE, width=2),
    ))

    fig.add_trace(go.Scatter(
        x=fitted.index, y=fitted.values, mode="lines", name=f"{model_name} Fit",
        line=dict(color=ORANGE, width=2, dash="dash"),
    ))

    fig.add_trace(go.Scatter(
        x=[next_date], y=[predicted_value], mode="markers", name="Forecast",
        marker=dict(color=VIOLET, size=12, symbol="diamond", line=dict(color="white", width=1)),
    ))

    fig.update_layout(
        title=f"{model_name}: Actual vs. Fitted vs. Forecast",
        dragmode="pan",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis_title="Price (USD)",
    )

    return fig
