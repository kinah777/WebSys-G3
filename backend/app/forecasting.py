from collections.abc import Sequence

from statsmodels.tsa.arima.model import ARIMA


MIN_ARIMA_OBSERVATIONS = 6


def forecast_monthly_series(
    observations: Sequence[tuple[str, float]],
    periods: int,
) -> dict[str, object]:
    """Fit ARIMA to ordered YYYY-MM observations and forecast future months."""
    monthly = {month: float(value) for month, value in observations}
    if not monthly:
        return {
            "status": "insufficient_history",
            "observations": [],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
        }

    first_year, first_month = (int(part) for part in min(monthly).split("-"))
    last_year, last_month = (int(part) for part in max(monthly).split("-"))
    month_index = first_year * 12 + first_month - 1
    last_index = last_year * 12 + last_month - 1
    history = []
    labels = []
    while month_index <= last_index:
        year, month_offset = divmod(month_index, 12)
        month = month_offset + 1
        label = f"{year:04d}-{month:02d}"
        labels.append(label)
        history.append(max(monthly.get(label, 0.0), 0.0))
        month_index += 1

    if len(monthly) < MIN_ARIMA_OBSERVATIONS:
        return {
            "status": "insufficient_history",
            "observations": [
                {"month": label, "value": value}
                for label, value in zip(labels, history)
            ],
            "forecast": [],
            "minimum_observations": MIN_ARIMA_OBSERVATIONS,
        }

    fitted = ARIMA(history, order=(1, 1, 1)).fit()
    predicted = fitted.forecast(steps=periods)
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
    }