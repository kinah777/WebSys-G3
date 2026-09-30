"""
Module 5: Financials & Cost Forecasting Router
==============================================
Manages project budgets, executive financial KPI summary calculations,
and the predictive burn-rate cost forecasting engine.

Endpoints:
- Budgets: GET /budgets, GET /budgets/{id}, GET /budgets/by-project/{project_id}, POST, PATCH, DELETE
- Complex: GET /financials/summary, GET /financials/forecast
"""

from datetime import date
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.database import Database, generate_next_id, serialize_row
from app.forecasting import forecast_daily_series, forecast_monthly_series
from .models import Budget, BudgetInput, CostHistoryInput, PartialBudgetInput

router = APIRouter(tags=["Module 5: Financials & Cost Forecasting"])


@router.post("/financials/cost-history", status_code=status.HTTP_201_CREATED, summary="Record an actual project cost")
def record_project_cost(data: CostHistoryInput, db: Database) -> dict[str, Any]:
    if data.incurred_on > date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cost date cannot be in the future")
    row = db.execute(
        """
        WITH inserted AS (
            INSERT INTO project_cost_history (project_id, amount, incurred_on, description)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        ), updated_budget AS (
            UPDATE budgets b
            SET actual_spending = COALESCE(b.actual_spending, 0) + i.amount,
                remaining_budget = COALESCE(b.allocated_budget, 0)
                    - (COALESCE(b.actual_spending, 0) + i.amount)
            FROM inserted i
            WHERE b.project_id = i.project_id
        )
        SELECT * FROM inserted
        """,
        [data.project_id, data.amount, data.incurred_on, data.description],
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record project cost",
        )
    return serialize_row(row)


@router.get("/financials/forecast/arima", summary="Forecast monthly project costs with ARIMA")
def arima_cost_forecast(
    db: Database,
    project_id: str | None = Query(None),
    periods: int = Query(3, ge=1, le=24),
) -> list[dict[str, Any]]:
    if project_id and not db.execute(
        "SELECT 1 FROM projects WHERE project_id = %s", [project_id]
    ).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    if project_id:
        projects = db.execute(
            "SELECT project_id, project_name FROM projects WHERE project_id = %s",
            [project_id],
        ).fetchall()
    else:
        projects = db.execute(
            """
            SELECT DISTINCT p.project_id, p.project_name
            FROM projects p
            JOIN project_cost_history h ON h.project_id = p.project_id
            ORDER BY p.project_id
            """
        ).fetchall()

    results = []
    for project in projects:
        rows = db.execute(
            """
            SELECT TO_CHAR(DATE_TRUNC('month', incurred_on), 'YYYY-MM') AS month,
                   SUM(amount) AS value
            FROM project_cost_history
            WHERE project_id = %s AND incurred_on <= CURRENT_DATE
            GROUP BY DATE_TRUNC('month', incurred_on)
            ORDER BY DATE_TRUNC('month', incurred_on)
            """,
            [project["project_id"]],
        ).fetchall()
        forecast = forecast_monthly_series(
            [(row["month"], float(row["value"])) for row in rows], periods
        )
        results.append({
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "status": forecast["status"],
            "currency": "PHP",
            "observations": forecast["observations"],
            "forecast": [
                {"month": point["month"], "projected_cost": point["value"]}
                for point in forecast["forecast"]
            ],
            "minimum_observations": forecast["minimum_observations"],
        })
    return results


# ==========================================================================
# 1. Budget Tracking Management
# ==========================================================================
@router.get("/budgets", response_model=list[Budget], summary="List all project budgets")
def list_budgets(
    db: Database,
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List approved project budgets and spending accounts."""
    rows = db.execute("SELECT * FROM budgets ORDER BY budget_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/budgets/{budget_id}", response_model=Budget, summary="Get budget by ID")
def get_budget(budget_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single budget record."""
    row = db.execute("SELECT * FROM budgets WHERE budget_id = %s", [budget_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Budget {budget_id} not found")
    return serialize_row(row)


@router.get("/budgets/by-project/{project_id}", response_model=Budget, summary="Get budget by project ID")
def get_budget_by_project(project_id: str, db: Database) -> dict[str, Any]:
    """Retrieve the budget record for a specific project."""
    row = db.execute("SELECT * FROM budgets WHERE project_id = %s", [project_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No budget found for project {project_id}")
    return serialize_row(row)


@router.post("/budgets", response_model=Budget, status_code=status.HTTP_201_CREATED, summary="Create a project budget")
def create_budget(data: BudgetInput, db: Database) -> dict[str, Any]:
    """Create a new project budget record with server-assigned ID (BUD-xxxx)."""
    if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [data.project_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found")

    existing = db.execute("SELECT budget_id FROM budgets WHERE project_id = %s", [data.project_id]).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Budget already exists for project {data.project_id} ({existing['budget_id']}). Use PATCH to update.",
        )

    remaining = data.allocated_budget - data.actual_spending
    new_id = generate_next_id(db, "budgets", "budget_id", "BUD-")
    db.execute(
        """
        INSERT INTO budgets (budget_id, project_id, allocated_budget, labor_cost, material_cost, equipment_cost, actual_spending, remaining_budget)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            new_id, data.project_id, data.allocated_budget, data.labor_cost,
            data.material_cost, data.equipment_cost, data.actual_spending, remaining,
        ],
    )
    return {**data.model_dump(), "remaining_budget": remaining, "budget_id": new_id}


@router.patch("/budgets/{budget_id}", response_model=Budget, summary="Partially update an existing budget")
def update_budget(budget_id: str, data: PartialBudgetInput, db: Database) -> dict[str, Any]:
    """
    Partial update: only the fields included in the request body will be changed.
    Remaining budget is automatically recalculated from allocated - actual.
    """
    existing = db.execute("SELECT * FROM budgets WHERE budget_id = %s", [budget_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Budget {budget_id} not found")

    merged_project_id = data.project_id if data.project_id is not None else existing["project_id"]
    merged_allocated = data.allocated_budget if data.allocated_budget is not None else float(existing["allocated_budget"] or 0)
    merged_labor = data.labor_cost if data.labor_cost is not None else float(existing["labor_cost"] or 0)
    merged_material = data.material_cost if data.material_cost is not None else float(existing["material_cost"] or 0)
    merged_equipment = data.equipment_cost if data.equipment_cost is not None else float(existing["equipment_cost"] or 0)
    merged_actual = data.actual_spending if data.actual_spending is not None else float(existing["actual_spending"] or 0)

    if merged_project_id != existing["project_id"]:
        if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [merged_project_id]).fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {merged_project_id} not found")

    remaining = merged_allocated - merged_actual
    db.execute(
        """
        UPDATE budgets
        SET project_id = %s, allocated_budget = %s, labor_cost = %s, material_cost = %s, equipment_cost = %s,
            actual_spending = %s, remaining_budget = %s
        WHERE budget_id = %s
        """,
        [
            merged_project_id, merged_allocated, merged_labor, merged_material, merged_equipment,
            merged_actual, remaining, budget_id,
        ],
    )
    return {
        "project_id": merged_project_id,
        "allocated_budget": merged_allocated,
        "labor_cost": merged_labor,
        "material_cost": merged_material,
        "equipment_cost": merged_equipment,
        "actual_spending": merged_actual,
        "remaining_budget": remaining,
        "budget_id": budget_id,
    }


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete budget")
def delete_budget(budget_id: str, db: Database) -> None:
    """Delete a budget record."""
    res = db.execute("DELETE FROM budgets WHERE budget_id = %s", [budget_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Budget {budget_id} not found")


# ==========================================================================
# 2. Financials KPI Summary & Cost Forecasting Engine
# ==========================================================================
@router.get("/financials/summary", summary="Executive portfolio financial summary KPIs")
def financials_summary(db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Executive overview calculating portfolio-wide totals: approved allocated budget,
    actual expenditures to date, net remaining funds, and count of projects currently in deficit (overrun).
    """
    row = db.execute(
        """
        SELECT
            COALESCE(SUM(allocated_budget), 0) AS total_allocated,
            COALESCE(SUM(actual_spending), 0)  AS total_spent,
            COALESCE(SUM(remaining_budget), 0) AS total_remaining,
            COUNT(*) FILTER (WHERE remaining_budget < 0) AS overrun_count
        FROM budgets
        """
    ).fetchone()
    return serialize_row(row) or {}


@router.get("/financials/forecast", summary="Daily project cost forecasts with ARIMA and budget burn-rate fallback")
def cost_forecast(
    db: Database,
    limit: int = Query(50, ge=1, le=500),
    forecast_days: int = Query(30, ge=1, le=90),
) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT b.*, p.project_name, p.start_date AS p_start, p.end_date AS p_end
        FROM budgets b
        JOIN projects p ON p.project_id = b.project_id
        ORDER BY b.budget_id
        LIMIT %s
        """,
        [limit],
    ).fetchall()

    today = date.today()
    results = []
    for r in rows:
        row = serialize_row(r)
        p_start = r["p_start"] or today
        p_end = r["p_end"] or today
        elapsed_days = max((today - p_start).days, 1)
        total_days = max((p_end - p_start).days, 1)
        remaining_days = max((p_end - today).days, 0)
        actual = float(r["actual_spending"] or 0)
        allocated = float(r["allocated_budget"] or 0)

        daily_burn = actual / elapsed_days
        history_rows = db.execute(
            """
            SELECT incurred_on::text AS day, SUM(amount) AS value
            FROM project_cost_history
            WHERE project_id = %s AND incurred_on <= CURRENT_DATE
            GROUP BY incurred_on
            ORDER BY incurred_on
            """,
            [r["project_id"]],
        ).fetchall()
        daily_forecast = forecast_daily_series(
            [(history["day"], float(history["value"])) for history in history_rows],
            periods=forecast_days,
            through_date=today,
        )

        forecast_method = "daily_arima"
        if daily_forecast["status"] == "ok" and daily_forecast["forecast"]:
            forecasted_daily_values = [
                point["value"] for point in daily_forecast["forecast"]
            ]
            forecasted_daily_average = sum(forecasted_daily_values) / len(forecasted_daily_values)
            projected_total = actual + forecasted_daily_average * remaining_days
        else:
            forecast_method = "burn_rate_fallback"
            projected_total = daily_burn * total_days

        projected_total = round(projected_total, 2)
        projected_overrun = round(projected_total - allocated, 2)

        results.append({
            **row,
            "daily_burn_rate": round(daily_burn, 2),
            "projected_total_cost": projected_total,
            "projected_overrun": projected_overrun,
            "is_overrun": projected_overrun > 0,
            "forecast_status": daily_forecast["status"],
            "forecast_method": forecast_method,
            "minimum_history_days": daily_forecast["minimum_observations"],
            "forecast_days": daily_forecast.get("effective_periods", 0),
        })
    return results
