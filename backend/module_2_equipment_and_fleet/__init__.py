"""
Module 2: Equipment & Fleet Management
======================================
Exposes router and Pydantic models for Module 2.
"""

from .models import (
    AssetStatus,
    AllocationStatus,
    MaintenanceStatus,
    AllocationStatusUpdate,
    Equipment,
    EquipmentInput,
    PartialEquipmentInput,
    Vehicle,
    VehicleInput,
    PartialVehicleInput,
    MaintenanceRecord,
    MaintenanceRecordInput,
    PartialMaintenanceRecordInput,
    EquipmentAllocation,
    EquipmentAllocationInput,
    PartialEquipmentAllocationInput,
    VehicleAllocation,
    VehicleAllocationInput,
    PartialVehicleAllocationInput,
)
from .router import router

__all__ = [
    "router",
    "AssetStatus",
    "AllocationStatus",
    "MaintenanceStatus",
    "AllocationStatusUpdate",
    "Equipment",
    "EquipmentInput",
    "PartialEquipmentInput",
    "Vehicle",
    "VehicleInput",
    "PartialVehicleInput",
    "MaintenanceRecord",
    "MaintenanceRecordInput",
    "PartialMaintenanceRecordInput",
    "EquipmentAllocation",
    "EquipmentAllocationInput",
    "PartialEquipmentAllocationInput",
    "VehicleAllocation",
    "VehicleAllocationInput",
    "PartialVehicleAllocationInput",
]
