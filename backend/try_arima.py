from app.forecasting import forecast_monthly_series

result = forecast_monthly_series(
    [(f"2025-{m:02d}", 10000 + m * 500) for m in range(1, 9)],
    periods=3
)
print(result)