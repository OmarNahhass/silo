from scipy import stats

import prediction_history
from model_registry import MODELS, ENSEMBLE_META
from utils.metrics import rmse, mae, mape

MIN_TTEST_SAMPLES = 20

_META_BY_KEY = {m["key"]: m for m in MODELS} | {ENSEMBLE_META["key"]: ENSEMBLE_META}


def _model_stats(rows: list[dict]) -> list[dict]:
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model_key"], []).append(row)

    stats_list = []
    for model_key, group in by_model.items():
        meta = _META_BY_KEY.get(model_key, {"name": model_key, "category": None})
        actual = [r["actual_close"] for r in group]
        predicted = [r["raw_prediction"] for r in group]
        stats_list.append(
            {
                "key": model_key,
                "name": meta["name"],
                "category": meta["category"],
                "n_samples": len(group),
                "rmse": rmse(actual, predicted),
                "mae": mae(actual, predicted),
                "mape": mape(actual, predicted),
            }
        )
    stats_list.sort(key=lambda s: s["rmse"])
    return stats_list


def _naive_baseline_and_test(ensemble_rows: list[dict]) -> tuple[dict | None, dict | None]:
    eligible = [r for r in ensemble_rows if r["prior_close"] is not None]
    if not eligible:
        return None, None

    actual = [r["actual_close"] for r in eligible]
    prior = [r["prior_close"] for r in eligible]
    naive_baseline = {
        "n_samples": len(eligible),
        "rmse": rmse(actual, prior),
        "mae": mae(actual, prior),
    }

    if len(eligible) < MIN_TTEST_SAMPLES:
        return naive_baseline, None

    diffs = [
        abs(r["actual_close"] - r["raw_prediction"]) - abs(r["actual_close"] - r["prior_close"])
        for r in eligible
    ]
    t_result = stats.ttest_1samp(diffs, popmean=0)
    t_statistic = float(t_result.statistic)
    p_value = float(t_result.pvalue)
    significant = p_value < 0.05

    if significant and t_statistic < 0:
        verdict = (
            f"The ensemble's absolute errors were significantly lower than the naive "
            f"no-change baseline's (paired t-test, p = {p_value:.4f}, n = {len(eligible)})."
        )
    elif significant:
        verdict = (
            f"The ensemble's absolute errors were significantly higher than the naive "
            f"no-change baseline's (paired t-test, p = {p_value:.4f}, n = {len(eligible)})."
        )
    else:
        verdict = (
            f"No statistically significant difference between the ensemble and the naive "
            f"no-change baseline (paired t-test, p = {p_value:.4f}, n = {len(eligible)})."
        )

    test = {
        "n_samples": len(eligible),
        "mean_abs_error_diff": sum(diffs) / len(diffs),
        "t_statistic": t_statistic,
        "p_value": p_value,
        "significant_at_0_05": significant,
        "verdict": verdict,
    }
    return naive_baseline, test


def get_track_record(ticker: str | None = None, asset_type: str | None = None, since: str | None = None) -> dict:
    rows = prediction_history.get_resolved_predictions(ticker=ticker, asset_type=asset_type, since=since)

    per_model = _model_stats(rows)
    ensemble_rows = [r for r in rows if r["model_key"] == "ensemble"]
    naive_baseline, ensemble_vs_naive_test = _naive_baseline_and_test(ensemble_rows)

    return {
        "scope": {"ticker": ticker, "asset_type": asset_type, "since": since},
        "per_model": per_model,
        "naive_baseline": naive_baseline,
        "ensemble_vs_naive_test": ensemble_vs_naive_test,
    }
