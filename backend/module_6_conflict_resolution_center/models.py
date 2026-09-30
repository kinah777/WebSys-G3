"""
Module 6: Resource Conflict Resolution Center Pydantic Models
=============================================================
Data schemas for conflict detection queries and resolution actions.
"""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field

AllocationType = Literal["equipment", "employee", "vehicle"]


class CancelAllocationInput(BaseModel):
    """Request body to cancel a conflicting allocation."""
    allocation_type: AllocationType = Field(description="Resource type: 'equipment', 'employee', or 'vehicle'")
    allocation_id: str = Field(description="ID of the allocation to cancel")


class RescheduleInput(BaseModel):
    """Request body to reschedule an allocation to new dates to resolve a conflict."""
    allocation_type: AllocationType = Field(description="Resource type: 'equipment', 'employee', or 'vehicle'")
    allocation_id: str = Field(description="ID of the allocation to reschedule")
    new_start_date: date = Field(description="New start date")
    new_end_date: date = Field(description="New end date")


class ReassignInput(BaseModel):
    """Request body to reassign an allocation to a different resource to resolve a conflict."""
    allocation_type: AllocationType = Field(description="Resource type: 'equipment', 'employee', or 'vehicle'")
    allocation_id: str = Field(description="ID of the allocation to reassign")
    new_resource_id: str = Field(description="New equipment_id, employee_id, or vehicle_id")


class ConflictSummary(BaseModel):
    """Badge counters for conflict center header."""
    equipment: int = Field(description="Number of active equipment overlap conflicts")
    employees: int = Field(description="Number of active worker overlap conflicts")
    vehicles: int = Field(description="Number of active vehicle overlap conflicts")
    total: int = Field(description="Total active conflicts across all categories")


class ResolutionResult(BaseModel):
    """Standardized response after executing a conflict resolution action."""
    status: str = Field(default="resolved")
    action: str = Field(description="Action performed: cancelled, rescheduled, or reassigned")
    allocation_id: str = Field(description="Target allocation ID")
    allocation_type: str = Field(description="equipment, employee, or vehicle")
