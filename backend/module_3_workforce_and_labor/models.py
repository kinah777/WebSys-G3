"""
Module 3: Workforce & Labor Management Pydantic Models
======================================================
Data schemas for internal employees, third-party contractors,
and worker project allocations.
Uses Literal types to enforce only valid status values from the seed dataset.
"""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


# Valid status values (must match seed data exactly)
EmploymentStatus = Literal["Active", "Inactive", "On Leave"]
ContractorStatus = Literal["Active", "Inactive"]
AllocationStatus = Literal["Scheduled", "Active", "Completed", "Cancelled"]


# --------------------------------------------------------------------------
# Typed Status Update Body
# --------------------------------------------------------------------------
class AllocationStatusUpdate(BaseModel):
    """Request body for changing an allocation's status."""
    allocation_status: AllocationStatus = Field(description="New status: Scheduled, Active, Completed, Cancelled")


# --------------------------------------------------------------------------
# Internal Employee Models
# --------------------------------------------------------------------------
class EmployeeInput(BaseModel):
    """Input payload for registering or updating an internal worker."""
    name: str = Field(min_length=1, max_length=150, description="Full employee name")
    position: str | None = Field(default=None, max_length=100, description="Job title / role (e.g. Civil Engineer, Site Foreman)")
    skill: str | None = Field(default=None, max_length=100, description="Primary skill / trade (e.g. Carpentry, Masonry, Welding)")
    phone: str | None = Field(default=None, max_length=30, description="Contact phone number")
    employment_status: EmploymentStatus = Field(default="Active", description="Active, Inactive, On Leave")
    daily_rate: float | None = Field(default=None, ge=0, description="Daily payroll rate in PHP")


class PartialEmployeeInput(BaseModel):
    """Partial update payload for PATCH. Only send fields that need changing."""
    name: str | None = Field(default=None, min_length=1, max_length=150, description="Full employee name")
    position: str | None = Field(default=None, max_length=100, description="Job title / role")
    skill: str | None = Field(default=None, max_length=100, description="Primary skill / trade")
    phone: str | None = Field(default=None, max_length=30, description="Contact phone number")
    employment_status: EmploymentStatus | None = Field(default=None, description="Active, Inactive, On Leave")
    daily_rate: float | None = Field(default=None, ge=0, description="Daily payroll rate in PHP")


class Employee(EmployeeInput):
    """Complete employee record including primary key."""
    employee_id: str = Field(description="Primary key (e.g. EMP-0001)")


# --------------------------------------------------------------------------
# External Contractor Models
# --------------------------------------------------------------------------
class ContractorInput(BaseModel):
    """Input payload for subcontracted firms and third-party labor vendors."""
    contractor_name: str = Field(min_length=1, max_length=150, description="Company or trade firm name")
    specialization: str | None = Field(default=None, max_length=100, description="Trade specialization (e.g. Electrical, Plumbing, Demolition)")
    contact_person: str | None = Field(default=None, max_length=150, description="Primary representative name")
    phone: str | None = Field(default=None, max_length=30, description="Contact phone number")
    rating: float | None = Field(default=None, ge=0, le=5, description="Performance evaluation rating (0.00 to 5.00)")
    status: ContractorStatus = Field(default="Active", description="Active, Inactive")


class PartialContractorInput(BaseModel):
    """Partial update payload for PATCH contractors. Only send fields that need changing."""
    contractor_name: str | None = Field(default=None, min_length=1, max_length=150, description="Company or trade firm name")
    specialization: str | None = Field(default=None, max_length=100, description="Trade specialization")
    contact_person: str | None = Field(default=None, max_length=150, description="Primary representative name")
    phone: str | None = Field(default=None, max_length=30, description="Contact phone number")
    rating: float | None = Field(default=None, ge=0, le=5, description="Performance evaluation rating")
    status: ContractorStatus | None = Field(default=None, description="Active, Inactive")


class Contractor(ContractorInput):
    """Complete contractor record including primary key."""
    contractor_id: str = Field(description="Primary key (e.g. CON-0001)")


# --------------------------------------------------------------------------
# Employee Allocation Models
# --------------------------------------------------------------------------
class EmployeeAllocationInput(BaseModel):
    """Input payload for assigning a worker to a construction project."""
    project_id: str = Field(min_length=1, description="Assigned project ID (e.g. PRJ-0001)")
    employee_id: str = Field(min_length=1, description="Assigned worker ID (e.g. EMP-0001)")
    start_date: date = Field(description="Assignment start date")
    end_date: date = Field(description="Assignment release date")
    role: str | None = Field(default=None, max_length=100, description="On-site assignment role")
    allocation_status: AllocationStatus = Field(default="Scheduled", description="Scheduled, Active, Completed, Cancelled")


class PartialEmployeeAllocationInput(BaseModel):
    """Partial update payload for PATCH employee allocations."""
    project_id: str | None = Field(default=None, min_length=1, description="Assigned project ID")
    employee_id: str | None = Field(default=None, min_length=1, description="Assigned worker ID")
    start_date: date | None = Field(default=None, description="Assignment start date")
    end_date: date | None = Field(default=None, description="Assignment release date")
    role: str | None = Field(default=None, max_length=100, description="On-site assignment role")
    allocation_status: AllocationStatus | None = Field(default=None, description="Scheduled, Active, Completed, Cancelled")


class EmployeeAllocation(EmployeeAllocationInput):
    """Complete employee allocation record including primary key."""
    employee_allocation_id: str = Field(description="Primary key (e.g. EMPA-0001)")
