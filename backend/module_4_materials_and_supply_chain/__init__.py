"""
Module 4: Materials & Supply Chain
==================================
Exposes router and Pydantic models for Module 4.
"""

from .models import (
    SupplierStatus,
    MaterialAllocationStatus,
    RestockInput,
    MaterialAllocationStatusUpdate,
    Material,
    MaterialInput,
    PartialMaterialInput,
    Supplier,
    SupplierInput,
    PartialSupplierInput,
    MaterialAllocation,
    MaterialAllocationInput,
)
from .router import router

__all__ = [
    "router",
    "SupplierStatus",
    "MaterialAllocationStatus",
    "RestockInput",
    "MaterialAllocationStatusUpdate",
    "Material",
    "MaterialInput",
    "PartialMaterialInput",
    "Supplier",
    "SupplierInput",
    "PartialSupplierInput",
    "MaterialAllocation",
    "MaterialAllocationInput",
]
