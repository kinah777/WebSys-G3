"""
Module 5: Financials & Cost Forecasting Pydantic Models
=======================================================
Data schemas for project budgets, cost allocation breakdowns,
and spending tracking.
"""

from pydantic import BaseModel, Field


class BudgetInput(BaseModel):
    """Input payload for creating a project budget account."""
    project_id: str = Field(min_length=1, description="Associated project ID (e.g. PRJ-0001)")
    allocated_budget: float = Field(ge=0, description="Total authorized budget limit in PHP")
    labor_cost: float = Field(default=0.0, ge=0, description="Estimated/allocated labor spend")
    material_cost: float = Field(default=0.0, ge=0, description="Estimated/allocated material spend")
    equipment_cost: float = Field(default=0.0, ge=0, description="Estimated/allocated equipment & plant spend")
    actual_spending: float = Field(default=0.0, ge=0, description="Cumulative actual expenses incurred so far")
    remaining_budget: float | None = Field(default=None, description="Calculated balance (allocated - actual)")


class PartialBudgetInput(BaseModel):
    """Partial update payload for PATCH budget. Only send fields that need changing."""
    project_id: str | None = Field(default=None, min_length=1, description="Associated project ID")
    allocated_budget: float | None = Field(default=None, ge=0, description="Total authorized budget limit in PHP")
    labor_cost: float | None = Field(default=None, ge=0, description="Estimated/allocated labor spend")
    material_cost: float | None = Field(default=None, ge=0, description="Estimated/allocated material spend")
    equipment_cost: float | None = Field(default=None, ge=0, description="Estimated/allocated equipment & plant spend")
    actual_spending: float | None = Field(default=None, ge=0, description="Cumulative actual expenses incurred so far")


class Budget(BudgetInput):
    """Complete budget record including primary key."""
    budget_id: str = Field(description="Primary key (e.g. BUD-0001)")
