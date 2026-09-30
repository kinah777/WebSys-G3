import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.forecasting import forecast_monthly_series


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