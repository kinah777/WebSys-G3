"""
Module 2: Equipment & Fleet Management Pydantic Models
======================================================
Data schemas for equipment units, fleet vehicles, maintenance logs,
and project allocation booking records.
Uses Literal types to enforce only valid status values from the seed dataset.
"""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


AssetStatus = Literal["Available", "In Use", "Maintenance", "Under Maintenance", "Retired"]
AllocationStatus = Literal["Scheduled", "Active", "Completed", "Cancelled"]
MaintenanceStatus = Literal["Scheduled", "In Progress", "Completed"]


# --------------------------------------------------------------------------
# Typed Status Update Body
# --------------------------------------------------------------------------
class AllocationStatusUpdate(BaseModel):
    """Request body for changing an allocation's status."""
    allocation_status: AllocationStatus = Field(description="New status: Scheduled, Active, Completed, Cancelled")


# --------------------------------------------------------------------------
# Equipment Asset Models
# --------------------------------------------------------------------------
class EquipmentInput(BaseModel):
    """Input payload for registering or updating heavy equipment machinery."""
    name: str = Field(min_length=1, max_length=150, description="Equipment machine name (e.g. Excavator CAT 320)")
    type: str | None = Field(default=None, max_length=100, description="Category (e.g. Earthmoving, Concrete, Crane)")
    model: str | None = Field(default=None, max_length=100, description="Manufacturer model identifier")
    status: AssetStatus = Field(default="Available", description="Available, In Use, Under Maintenance, Retired")
    daily_rental_cost: float | None = Field(default=None, ge=0, description="Daily rate in PHP")
    purchase_value: float | None = Field(default=None, ge=0, description="Acquisition or replacement asset value")


class PartialEquipmentInput(BaseModel):
    """Partial update payload for PATCH equipment. Only send fields that need changing."""
    name: str | None = Field(default=None, min_length=1, max_length=150, description="Equipment machine name")
    type: str | None = Field(default=None, max_length=100, description="Category")
    model: str | None = Field(default=None, max_length=100, description="Manufacturer model identifier")
    status: AssetStatus | None = Field(default=None, description="Available, In Use, Under Maintenance, Retired")
    daily_rental_cost: float | None = Field(default=None, ge=0, description="Daily rate in PHP")
    purchase_value: float | None = Field(default=None, ge=0, description="Acquisition or replacement asset value")


class Equipment(EquipmentInput):
    """Complete equipment asset record including primary key."""
    equipment_id: str = Field(description="Primary key (e.g. EQ-0001)")


# --------------------------------------------------------------------------
# Vehicle Fleet Models
# --------------------------------------------------------------------------
class VehicleInput(BaseModel):
    """Input payload for registering or updating a fleet vehicle."""
    vehicle_type: str | None = Field(default=None, max_length=100, description="Dump Truck, Pickup, Van, Mixer")
    plate_number: str = Field(min_length=1, max_length=30, description="Unique registration plate number")
    driver: str | None = Field(default=None, max_length=150, description="Assigned primary driver name")
    status: AssetStatus = Field(default="Available", description="Available, In Use, Under Maintenance, Retired")
    daily_operating_cost: float | None = Field(default=None, ge=0, description="Daily fuel & operational cost")


class PartialVehicleInput(BaseModel):
    """Partial update payload for PATCH vehicles. Only send fields that need changing."""
    vehicle_type: str | None = Field(default=None, max_length=100, description="Dump Truck, Pickup, Van, Mixer")
    plate_number: str | None = Field(default=None, min_length=1, max_length=30, description="Registration plate number")
    driver: str | None = Field(default=None, max_length=150, description="Assigned primary driver name")
    status: AssetStatus | None = Field(default=None, description="Available, In Use, Under Maintenance, Retired")
    daily_operating_cost: float | None = Field(default=None, ge=0, description="Daily fuel & operational cost")


class Vehicle(VehicleInput):
    """Complete vehicle record including primary key."""
    vehicle_id: str = Field(description="Primary key (e.g. VEH-0001)")


# --------------------------------------------------------------------------
# Maintenance Log Models
# --------------------------------------------------------------------------
class MaintenanceRecordInput(BaseModel):
    """Input payload for scheduling or logging an equipment maintenance downtime event."""
    equipment_id: str = Field(min_length=1, description="Equipment asset ID (e.g. EQ-0001)")
    maintenance_date: date | None = Field(default=None, description="Service start date")
    maintenance_type: str | None = Field(default=None, max_length=100, description="Preventive, Corrective, Overhaul")
    maintenance_cost: float | None = Field(default=None, ge=0, description="Direct repair/maintenance cost")
    duration_days: int | None = Field(default=None, ge=0, description="Expected downtime in days")
    maintenance_status: MaintenanceStatus = Field(default="Scheduled", description="Scheduled, In Progress, Completed")


class PartialMaintenanceRecordInput(BaseModel):
    """Partial update payload for PATCH maintenance records. Only send fields that need changing."""
    equipment_id: str | None = Field(default=None, min_length=1, description="Equipment asset ID")
    maintenance_date: date | None = Field(default=None, description="Service start date")
    maintenance_type: str | None = Field(default=None, max_length=100, description="Preventive, Corrective, Overhaul")
    maintenance_cost: float | None = Field(default=None, ge=0, description="Direct repair/maintenance cost")
    duration_days: int | None = Field(default=None, ge=0, description="Expected downtime in days")
    maintenance_status: MaintenanceStatus | None = Field(default=None, description="Scheduled, In Progress, Completed")


class MaintenanceRecord(MaintenanceRecordInput):
    """Complete maintenance log record including primary key."""
    maintenance_id: str = Field(description="Primary key (e.g. MNT-0001)")


# --------------------------------------------------------------------------
# Allocation Booking Models (Equipment & Fleet)
# --------------------------------------------------------------------------
class EquipmentAllocationInput(BaseModel):
    """Input payload for booking an equipment asset on a project."""
    project_id: str = Field(min_length=1, description="Target project ID (e.g. PRJ-0001)")
    equipment_id: str = Field(min_length=1, description="Booked equipment asset ID (e.g. EQ-0001)")
    start_date: date = Field(description="Booking commencement date")
    end_date: date = Field(description="Booking completion date")
    purpose: str | None = Field(default=None, max_length=150, description="Site task purpose (e.g. Excavation)")
    allocation_status: AllocationStatus = Field(default="Scheduled", description="Scheduled, Active, Completed, Cancelled")


class PartialEquipmentAllocationInput(BaseModel):
    """Partial update payload for PATCH equipment allocations."""
    project_id: str | None = Field(default=None, min_length=1, description="Target project ID")
    equipment_id: str | None = Field(default=None, min_length=1, description="Booked equipment asset ID")
    start_date: date | None = Field(default=None, description="Booking commencement date")
    end_date: date | None = Field(default=None, description="Booking completion date")
    purpose: str | None = Field(default=None, max_length=150, description="Site task purpose")
    allocation_status: AllocationStatus | None = Field(default=None, description="Scheduled, Active, Completed, Cancelled")


class EquipmentAllocation(EquipmentAllocationInput):
    """Complete equipment booking record including primary key."""
    allocation_id: str = Field(description="Primary key (e.g. EA-0001)")


class VehicleAllocationInput(BaseModel):
    """Input payload for allocating a vehicle to a project."""
    project_id: str = Field(min_length=1, description="Target project ID (e.g. PRJ-0001)")
    vehicle_id: str = Field(min_length=1, description="Allocated vehicle ID (e.g. VEH-0001)")
    start_date: date = Field(description="Allocation start date")
    end_date: date = Field(description="Allocation end date")
    purpose: str | None = Field(default=None, max_length=150, description="Transport / haulage purpose")
    allocation_status: AllocationStatus = Field(default="Scheduled", description="Scheduled, Active, Completed, Cancelled")


class PartialVehicleAllocationInput(BaseModel):
    """Partial update payload for PATCH vehicle allocations."""
    project_id: str | None = Field(default=None, min_length=1, description="Target project ID")
    vehicle_id: str | None = Field(default=None, min_length=1, description="Allocated vehicle ID")
    start_date: date | None = Field(default=None, description="Allocation start date")
    end_date: date | None = Field(default=None, description="Allocation end date")
    purpose: str | None = Field(default=None, max_length=150, description="Transport / haulage purpose")
    allocation_status: AllocationStatus | None = Field(default=None, description="Scheduled, Active, Completed, Cancelled")


class VehicleAllocation(VehicleAllocationInput):
    """Complete vehicle booking record including primary key."""
    vehicle_allocation_id: str = Field(description="Primary key (e.g. VA-0001)")
