"""
Module 4: Materials & Supply Chain Pydantic Models
==================================================
Data schemas for inventory materials, vendor suppliers,
and project material allocations.
Uses Literal types to enforce only valid status values from the seed dataset.
"""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


SupplierStatus = Literal["Active", "Inactive"]
MaterialAllocationStatus = Literal["Pending", "Ordered", "Delivered", "Used", "Scheduled", "Active", "Completed", "Cancelled"]


# --------------------------------------------------------------------------
# Restock & Status Request Models
# --------------------------------------------------------------------------
class RestockInput(BaseModel):
    """Request body for restocking a material with incoming shipment."""
    quantity: float = Field(gt=0, description="Quantity of units to add to inventory")
    unit_cost: float | None = Field(default=None, ge=0, description="Optional updated unit cost")


class MaterialAllocationStatusUpdate(BaseModel):
    """Request body for changing a material allocation's status."""
    status: MaterialAllocationStatus = Field(description="New status: Scheduled, Active, Completed, Cancelled")


# --------------------------------------------------------------------------
# Material Inventory Models
# --------------------------------------------------------------------------
class MaterialInput(BaseModel):
    """Input payload for adding or editing a construction material catalog item."""
    name: str = Field(min_length=1, max_length=150, description="Material item name (e.g. Portland Cement Type 1)")
    type: str | None = Field(default=None, max_length=100, description="Category (e.g. Concrete, Steel, Aggregates)")
    unit: str | None = Field(default=None, max_length=50, description="Unit of measure (e.g. bags, tons, cu.m, meters)")
    quantity_in_stock: float = Field(default=0.0, ge=0, description="Current warehouse/site stock volume")
    reorder_level: float = Field(default=0.0, ge=0, description="Minimum inventory threshold before triggering reorder alert")
    unit_cost: float = Field(default=0.0, ge=0, description="Unit purchase cost in PHP")


class PartialMaterialInput(BaseModel):
    """Partial update payload for PATCH materials. Only send fields that need changing."""
    name: str | None = Field(default=None, min_length=1, max_length=150, description="Material item name")
    type: str | None = Field(default=None, max_length=100, description="Category")
    unit: str | None = Field(default=None, max_length=50, description="Unit of measure")
    quantity_in_stock: float | None = Field(default=None, ge=0, description="Current stock volume")
    reorder_level: float | None = Field(default=None, ge=0, description="Reorder threshold")
    unit_cost: float | None = Field(default=None, ge=0, description="Unit purchase cost in PHP")


class Material(MaterialInput):
    """Complete material inventory record including primary key."""
    material_id: str = Field(description="Primary key (e.g. MAT-0001)")


# --------------------------------------------------------------------------
# Material Supplier Models
# --------------------------------------------------------------------------
class SupplierInput(BaseModel):
    """Input payload for registering or updating a material supplier."""
    name: str = Field(min_length=1, max_length=150, description="Supplier company name")
    contact_person: str | None = Field(default=None, max_length=150, description="Key account contact person")
    phone: str | None = Field(default=None, max_length=30, description="Sales / orders phone number")
    location: str | None = Field(default=None, max_length=150, description="Warehouse or office location")
    supplier_rating: float | None = Field(default=None, ge=0, le=5, description="Reliability score (0.00 to 5.00)")
    status: SupplierStatus = Field(default="Active", description="Active, Inactive")


class PartialSupplierInput(BaseModel):
    """Partial update payload for PATCH suppliers. Only send fields that need changing."""
    name: str | None = Field(default=None, min_length=1, max_length=150, description="Supplier company name")
    contact_person: str | None = Field(default=None, max_length=150, description="Key account contact person")
    phone: str | None = Field(default=None, max_length=30, description="Phone number")
    location: str | None = Field(default=None, max_length=150, description="Location")
    supplier_rating: float | None = Field(default=None, ge=0, le=5, description="Reliability score")
    status: SupplierStatus | None = Field(default=None, description="Active, Inactive")


class Supplier(SupplierInput):
    """Complete supplier record including primary key."""
    supplier_id: str = Field(description="Primary key (e.g. SUP-0001)")


# --------------------------------------------------------------------------
# Material Allocation Models
# --------------------------------------------------------------------------
class MaterialAllocationInput(BaseModel):
    """Input payload for requisitioning materials for a construction project."""
    project_id: str = Field(min_length=1, description="Target project ID (e.g. PRJ-0001)")
    material_id: str = Field(min_length=1, description="Requisitioned material ID (e.g. MAT-0001)")
    quantity_required: float = Field(gt=0, description="Quantity requested for the project")
    quantity_used: float = Field(default=0.0, ge=0, description="Quantity actually consumed so far")
    required_date: date | None = Field(default=None, description="Date needed on site")
    status: MaterialAllocationStatus = Field(default="Scheduled", description="Scheduled, Active, Completed, Cancelled")


class MaterialAllocation(MaterialAllocationInput):
    """Complete material allocation record including primary key."""
    material_allocation_id: str = Field(description="Primary key (e.g. MA-0001)")
