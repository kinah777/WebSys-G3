"""
Module 1: Projects & Schedules Pydantic Models
==============================================
Data schemas for project records and schedule milestone tasks.
Uses Literal types to enforce only valid status values from the seed dataset.
"""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


ProjectStatus = Literal["Planning", "Ongoing", "Completed", "On Hold"]
ScheduleStatus = Literal["Pending", "Not Started", "In Progress", "Completed"]
PriorityLevel = Literal["Critical", "High", "Medium", "Low"]


class ProjectInput(BaseModel):
    """Input payload for creating a construction project. All essential fields required."""
    project_name: str = Field(min_length=1, max_length=150, description="Full name of the project")
    project_type: str | None = Field(default=None, max_length=100, description="e.g. Commercial, Residential, Infrastructure")
    location: str | None = Field(default=None, max_length=150, description="Site location / city")
    start_date: date | None = Field(default=None, description="Planned project start date")
    end_date: date | None = Field(default=None, description="Planned project target completion date")
    budget: float | None = Field(default=None, ge=0, description="Total allocated budget in PHP")
    priority: PriorityLevel | None = Field(default=None, description="Priority level: High, Medium, Low")
    status: ProjectStatus = Field(default="Planning", description="Planning, Ongoing, Completed, On Hold")
    completion_percentage: float | None = Field(default=0.0, ge=0, le=100, description="0 to 100 progress percent")


class PartialProjectInput(BaseModel):
    """Partial update payload for PATCH. All fields optional so only changed fields need to be sent."""
    project_name: str | None = Field(default=None, min_length=1, max_length=150, description="Full name of the project")
    project_type: str | None = Field(default=None, max_length=100, description="e.g. Commercial, Residential, Infrastructure")
    location: str | None = Field(default=None, max_length=150, description="Site location / city")
    start_date: date | None = Field(default=None, description="Planned project start date")
    end_date: date | None = Field(default=None, description="Planned project target completion date")
    budget: float | None = Field(default=None, ge=0, description="Total allocated budget")
    priority: PriorityLevel | None = Field(default=None, description="Priority level: High, Medium, Low")
    status: ProjectStatus | None = Field(default=None, description="Planning, Ongoing, Completed, On Hold")
    completion_percentage: float | None = Field(default=None, ge=0, le=100, description="0 to 100 progress percent")


class Project(ProjectInput):
    """Complete project record including the primary key."""
    project_id: str = Field(description="Primary key (e.g. PRJ-0001)")


class ScheduleInput(BaseModel):
    """Input payload for a schedule milestone task."""
    project_id: str = Field(min_length=1, description="Associated project ID (e.g. PRJ-0001)")
    task_name: str = Field(min_length=1, max_length=150, description="Name or milestone description")
    start_date: date | None = Field(default=None, description="Task start date")
    end_date: date | None = Field(default=None, description="Task target end date")
    duration_days: int | None = Field(default=None, ge=0, description="Duration in calendar days")
    dependency: str | None = Field(default=None, max_length=100, description="Precedent task name or ID")
    status: ScheduleStatus = Field(default="Pending", description="Pending, In Progress, Completed")


class PartialScheduleInput(BaseModel):
    """Partial update payload for PATCH schedule tasks. All fields optional."""
    project_id: str | None = Field(default=None, min_length=1, description="Associated project ID")
    task_name: str | None = Field(default=None, min_length=1, max_length=150, description="Name or milestone description")
    start_date: date | None = Field(default=None, description="Task start date")
    end_date: date | None = Field(default=None, description="Task target end date")
    duration_days: int | None = Field(default=None, ge=0, description="Duration in calendar days")
    dependency: str | None = Field(default=None, max_length=100, description="Precedent task name or ID")
    status: ScheduleStatus | None = Field(default=None, description="Pending, In Progress, Completed")


class Schedule(ScheduleInput):
    """Complete schedule task record including the primary key."""
    schedule_id: str = Field(description="Primary key (e.g. SCH-0001)")
