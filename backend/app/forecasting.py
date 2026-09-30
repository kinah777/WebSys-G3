import math
import warnings
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ModelWarning


MIN_ARIMA_OBSERVATIONS = 6
MIN_DAILY_ARIMA_OBSERVATIONS = 30
MAX_DAILY_FORECAST_DAYS = 90


def _build_monthly_series(observations: Sequence[tuple[str, float]]) -> tuple[list[str], list[float]]:
    monthly: dict[str, float] = {}
    for month, value in observations:
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError(f"Observation for {month} is not finite: {value!r}")
        monthly[str(month)] = numeric

    if not monthly:
        return [], []

    first_year, first_month = (int(part) for part in min(monthly).split("-"))
    last_year, last_month = (int(part) for part in max(monthly).split("-"))
    month_index = first_year * 12 + first_month - 1
    last_index = last_year * 12 + last_month - 1

    labels: list[str] = []
    history: list[float] = []
    while month_index <= last_index:
        year, month_offset = divmod(month_index, 12)
        month = month_offset + 1
        label = f"{year:04d}-{month:02d}"
        labels.append(label)
        history.append(max(monthly.get(label, 0.0), 0.0))
        month_index += 1

    return labels, history


def forecast_monthly_series(
    observations: Sequence[tuple[str, float]],
    periods: int,
) -> dict[str, Any]:
    """Fit a practical ARIMA model to ordered YYYY-MM observations and forecast future months."""
    if not observations:
        return {
            "status": "insufficient_history",
            "observations": [],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
        }

    try:
        labels, history = _build_monthly_series(observations)
    except ValueError:
        return {
            "status": "forecast_failed",
            "observations": [],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
            "error": "Encountered a non-finite value in the observed series",
        }

    if len(history) < MIN_ARIMA_OBSERVATIONS:
        return {
            "status": "insufficient_history",
            "observations": [
                {"month": label, "value": value}
                for label, value in zip(labels, history)
            ],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
        }

    requested_periods = max(1, int(periods))
    safe_horizon = max(1, len(history) // 2)
    forecast_steps = min(requested_periods, safe_horizon)

    best_fit = None
    best_aic = None
    for p in range(3):
        for d in (0, 1):
            for q in range(3):
                order = (p, d, q)
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=Warning)
                        warnings.filterwarnings("ignore", category=ModelWarning)
                        candidate = ARIMA(history, order=order).fit()
                    aic = float(candidate.aic)
                    if best_aic is None or aic < best_aic:
                        best_fit = candidate
                        best_aic = aic
                except Exception:
                    continue

    if best_fit is None:
        return {
            "status": "forecast_failed",
            "observations": [
                {"month": label, "value": value}
                for label, value in zip(labels, history)
            ],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
            "error": "ARIMA fit failed for all tested model orders",
        }

    predicted = best_fit.forecast(steps=forecast_steps)
    last_index = (int(labels[-1].split("-")[0]) * 12 + int(labels[-1].split("-")[1])) - 1
    forecast = []
    for offset, value in enumerate(predicted, start=1):
        year, month_offset = divmod(last_index + offset, 12)
        forecast.append({
            "month": f"{year:04d}-{month_offset + 1:02d}",
            "value": round(max(float(value), 0.0), 2),
        })

    return {
        "status": "ok",
        "observations": [
            {"month": label, "value": value}
            for label, value in zip(labels, history)
        ],
        "forecast": forecast,
        "minimum_observations": MIN_ARIMA_OBSERVATIONS,
        "requested_periods": requested_periods,
        "effective_periods": forecast_steps,
    }


def _build_daily_series(
    observations: Sequence[tuple[str, float]],
    through_date: date | None = None,
) -> tuple[list[str], list[float]]:
    daily: dict[date, float] = {}
    for day_label, value in observations:
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError(f"Observation for {day_label} is not finite: {value!r}")
        day = date.fromisoformat(str(day_label))
        daily[day] = daily.get(day, 0.0) + numeric

    if not daily:
        return [], []

    first_day = min(daily)
    last_day = max(max(daily), through_date or max(daily))
    labels: list[str] = []
    history: list[float] = []
    current_day = first_day
    while current_day <= last_day:
        labels.append(current_day.isoformat())
        history.append(max(daily.get(current_day, 0.0), 0.0))
        current_day += timedelta(days=1)

    return labels, history


def forecast_daily_series(
    observations: Sequence[tuple[str, float]],
    periods: int,
    through_date: date | None = None,
) -> dict[str, Any]:
    """Fit ARIMA to daily YYYY-MM-DD totals, treating no-expense days as zero."""
    if not observations:
        return {
            "status": "insufficient_history",
            "observations": [],
            "forecast": [],
            "minimum_observations": MIN_DAILY_ARIMA_OBSERVATIONS,
        }

    try:
        labels, history = _build_daily_series(observations, through_date)
    except ValueError:
        return {
            "status": "forecast_failed",
            "observations": [],
            "forecast": [],
            "minimum_observations": MIN_DAILY_ARIMA_OBSERVATIONS,
            "error": "Encountered an invalid date or non-finite value in the observed series",
        }

    observed = [
        {"day": label, "value": value}
        for label, value in zip(labels, history)
    ]
    if len(history) < MIN_DAILY_ARIMA_OBSERVATIONS:
        return {
            "status": "insufficient_history",
            "observations": observed,
            "forecast": [],
            "minimum_observations": MIN_DAILY_ARIMA_OBSERVATIONS,
        }

    requested_periods = min(max(1, int(periods)), MAX_DAILY_FORECAST_DAYS)
    forecast_steps = min(requested_periods, max(1, len(history) // 2))
    best_fit = None
    best_aic = None
    for p in range(3):
        for d in (0, 1):
            for q in range(3):
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=Warning)
                        warnings.filterwarnings("ignore", category=ModelWarning)
                        candidate = ARIMA(history, order=(p, d, q)).fit()
                    aic = float(candidate.aic)
                    if best_aic is None or aic < best_aic:
                        best_fit = candidate
                        best_aic = aic
                except Exception:
                    continue

    if best_fit is None:
        return {
            "status": "forecast_failed",
            "observations": observed,
            "forecast": [],
            "minimum_observations": MIN_DAILY_ARIMA_OBSERVATIONS,
            "error": "ARIMA fit failed for all tested model orders",
        }

    predicted = best_fit.forecast(steps=forecast_steps)
    last_day = date.fromisoformat(labels[-1])
    forecast = [
        {
            "day": (last_day + timedelta(days=offset)).isoformat(),
            "value": round(max(float(value), 0.0), 2),
        }
        for offset, value in enumerate(predicted, start=1)
    ]
    return {
        "status": "ok",
        "observations": observed,
        "forecast": forecast,
        "minimum_observations": MIN_DAILY_ARIMA_OBSERVATIONS,
        "requested_periods": requested_periods,
        "effective_periods": forecast_steps,
    }