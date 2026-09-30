from datetime import date, timedelta
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.forecasting import forecast_daily_series, forecast_monthly_series


def test_forecast_monthly_series_fits_arima_and_labels_future_months():
    observations = [
        (f"2025-{month:02d}", float(month * 10))
        for month in range(1, 9)
    ]

    result = forecast_monthly_series(observations, periods=3)

    assert result["status"] == "ok"
    assert [point["month"] for point in result["forecast"]] == [
        "2025-09", "2025-10", "2025-11"
    ]
    assert all(point["value"] >= 0 for point in result["forecast"])


def test_forecast_monthly_series_fills_missing_months_with_zero():
    result = forecast_monthly_series(
        [("2025-01", 10.0), ("2025-03", 30.0)], periods=1
    )

    assert result["status"] == "insufficient_history"
    assert result["observations"] == [
        {"month": "2025-01", "value": 10.0},
        {"month": "2025-02", "value": 0.0},
        {"month": "2025-03", "value": 30.0},
    ]
    assert result["forecast"] == []


def test_forecast_monthly_series_requires_six_observed_months():
    result = forecast_monthly_series(
        [(f"2025-{month:02d}", float(month)) for month in range(1, 6)],
        periods=2,
    )

    assert result["status"] == "insufficient_history"
    assert result["minimum_observations"] == 6
    assert result["forecast"] == []


def test_forecast_monthly_series_returns_failed_status_when_fit_fails():
    result = forecast_monthly_series(
        [("2025-01", float("nan")), ("2025-02", 1.0), ("2025-03", 2.0),
         ("2025-04", 3.0), ("2025-05", 4.0), ("2025-06", 5.0)],
        periods=2,
    )

    assert result["status"] == "forecast_failed"
    assert result["forecast"] == []


def test_forecast_monthly_series_caps_horizon_to_observation_length_half():
    observations = [(f"2025-{month:02d}", float(month * 10)) for month in range(1, 7)]

    result = forecast_monthly_series(observations, periods=12)

    assert result["status"] == "ok"
    assert len(result["forecast"]) == 3


def test_forecast_daily_series_fits_and_labels_future_days():
    start = date(2026, 1, 1)
    observations = [
        ((start + timedelta(days=offset)).isoformat(), float(100 + offset))
        for offset in range(30)
    ]

    result = forecast_daily_series(
        observations,
        periods=3,
        through_date=start + timedelta(days=29),
    )

    assert result["status"] == "ok"
    assert [point["day"] for point in result["forecast"]] == [
        "2026-01-31", "2026-02-01", "2026-02-02"
    ]
    assert all(point["value"] >= 0 for point in result["forecast"])


def test_forecast_daily_series_fills_no_expense_days_and_requires_thirty_days():
    result = forecast_daily_series(
        [("2026-01-01", 10.0), ("2026-01-03", 30.0)],
        periods=2,
        through_date=date(2026, 1, 3),
    )

    assert result["status"] == "insufficient_history"
    assert result["minimum_observations"] == 30
    assert result["observations"] == [
        {"day": "2026-01-01", "value": 10.0},
        {"day": "2026-01-02", "value": 0.0},
        {"day": "2026-01-03", "value": 30.0},
    ]
    assert result["forecast"] == []