# Module 5: Financials & Cost Forecasting

This module manages project budgets, executive portfolio financial KPIs, and predictive burn-rate cost forecasting.

## Database Tables
- `budgets` (ID prefix: `BUD-`, e.g., `BUD-0001`)

## Endpoints

### Budgets
- `GET /budgets` - List all project budgets
- `GET /budgets/{budget_id}` - Retrieve details of a specific budget
- `GET /budgets/by-project/{project_id}` - Retrieve budget for a specific project
- `POST /budgets` - Create a project budget (auto-generates `BUD-xxxx`, calculates `remaining_budget = allocated - actual`)
- `PATCH /budgets/{budget_id}` - Partial update of budget values (auto-recalculates `remaining_budget`)
- `DELETE /budgets/{budget_id}` - Delete budget record

### Complex Endpoints
- `GET /financials/summary` - Returns portfolio-wide KPIs: total allocated budget, total spending to date, remaining budget balance, and count of projects in deficit/overrun.
- `GET /financials/forecast` - Returns predictive cost projections using elapsed days, daily burn rate (`actual_spending / elapsed_days`), projected total completion cost, and estimated budget overruns.
- `POST /financials/cost-history` - Record a dated actual project cost in PHP.
- `GET /financials/forecast/arima?project_id=PRJ-0001&periods=3` - Forecast monthly project costs with ARIMA. Omitting `project_id` returns forecasts for projects with recorded history. Each project needs at least six distinct months of history.
