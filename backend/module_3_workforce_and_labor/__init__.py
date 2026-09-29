"""
Module 3: Workforce & Labor Management
======================================
Exposes router and Pydantic models for Module 3.
"""

from .models import (
    EmploymentStatus,
    ContractorStatus,
    AllocationStatus,
    AllocationStatusUpdate,
    Employee,
    EmployeeInput,
    PartialEmployeeInput,
    Contractor,
    ContractorInput,
    PartialContractorInput,
    EmployeeAllocation,
    EmployeeAllocationInput,
    PartialEmployeeAllocationInput,
)
from .router import router

__all__ = [
    "router",
    "EmploymentStatus",
    "ContractorStatus",
    "AllocationStatus",
    "AllocationStatusUpdate",
    "Employee",
    "EmployeeInput",
    "PartialEmployeeInput",
    "Contractor",
    "ContractorInput",
    "PartialContractorInput",
    "EmployeeAllocation",
    "EmployeeAllocationInput",
    "PartialEmployeeAllocationInput",
]
