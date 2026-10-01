"""
Module 2: Equipment & Fleet Management Router
=============================================
Manages heavy machinery, fleet vehicles, maintenance downtime records,
and equipment/vehicle project allocation schedules.

Endpoints:
- Equipment: GET /equipment, GET /equipment/{id}, POST, PATCH, DELETE
- Vehicles: GET /vehicles, GET /vehicles/{id}, POST, PATCH, DELETE
- Maintenance: GET /maintenance-records (and /maintenance), POST, DELETE (auto-sets status to 'Under Maintenance')
- Allocations: GET, POST (with conflict check), PATCH (reschedule), PATCH status, DELETE for equipment & vehicles
"""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.database import Database, generate_next_id, serialize_row
from .models import (
    AllocationStatusUpdate,
    Equipment,
    EquipmentAllocation,
    EquipmentAllocationInput,
    EquipmentInput,
    MaintenanceRecord,
    MaintenanceRecordInput,
    PartialEquipmentAllocationInput,
    PartialEquipmentInput,
    PartialVehicleAllocationInput,
    PartialVehicleInput,
    Vehicle,
    VehicleAllocation,
    VehicleAllocationInput,
    VehicleInput,
)

router = APIRouter(tags=["Module 2: Equipment & Fleet Management"])


# ==========================================================================
# 1. Equipment Management
# ==========================================================================
@router.get("/equipment", response_model=list[Equipment], summary="List all equipment")
def list_equipment(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Available, In Use, Under Maintenance, Retired"),
    limit: int = Query(600, ge=1, le=600),
) -> list[dict[str, Any]]:
    """List construction equipment units with optional status filter."""
    if filter_status:
        rows = db.execute(
            "SELECT * FROM equipment WHERE status = %s ORDER BY equipment_id LIMIT %s",
            [filter_status, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM equipment ORDER BY equipment_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/equipment/{equipment_id}", response_model=Equipment, summary="Get equipment details by ID")
def get_equipment(equipment_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single equipment unit."""
    row = db.execute("SELECT * FROM equipment WHERE equipment_id = %s", [equipment_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found")
    return serialize_row(row)


@router.post("/equipment", response_model=Equipment, status_code=status.HTTP_201_CREATED, summary="Create new equipment")
def create_equipment(data: EquipmentInput, db: Database) -> dict[str, Any]:
    """Register a new equipment asset with server-assigned ID (EQ-xxxx)."""
    new_id = generate_next_id(db, "equipment", "equipment_id", "EQ-")
    db.execute(
        """
        INSERT INTO equipment (equipment_id, name, type, model, status, daily_rental_cost, purchase_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.name, data.type, data.model, data.status, data.daily_rental_cost, data.purchase_value],
    )
    return {**data.model_dump(), "equipment_id": new_id}


@router.patch("/equipment/{equipment_id}", response_model=Equipment, summary="Partially update equipment details")
def update_equipment(equipment_id: str, data: PartialEquipmentInput, db: Database) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM equipment WHERE equipment_id = %s", [equipment_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found")

    merged = {
        "name": data.name if data.name is not None else existing["name"],
        "type": data.type if data.type is not None else existing["type"],
        "model": data.model if data.model is not None else existing["model"],
        "status": data.status if data.status is not None else existing["status"],
        "daily_rental_cost": data.daily_rental_cost if data.daily_rental_cost is not None else existing["daily_rental_cost"],
        "purchase_value": data.purchase_value if data.purchase_value is not None else existing["purchase_value"],
    }
    db.execute(
        """
        UPDATE equipment
        SET name = %s, type = %s, model = %s, status = %s, daily_rental_cost = %s, purchase_value = %s
        WHERE equipment_id = %s
        """,
        [merged["name"], merged["type"], merged["model"], merged["status"], merged["daily_rental_cost"], merged["purchase_value"], equipment_id],
    )
    return {**merged, "equipment_id": equipment_id}


@router.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete equipment")
def delete_equipment(equipment_id: str, db: Database) -> None:
    """Delete an equipment unit and its associated allocations."""
    res = db.execute("DELETE FROM equipment WHERE equipment_id = %s", [equipment_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found")


# ==========================================================================
# 2. Fleet & Vehicles Management
# ==========================================================================
@router.get("/vehicles", response_model=list[Vehicle], summary="List all fleet vehicles")
def list_vehicles(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Available, In Use, Under Maintenance, Retired"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List fleet vehicles with optional status filter."""
    if filter_status:
        rows = db.execute(
            "SELECT * FROM vehicles WHERE status = %s ORDER BY vehicle_id LIMIT %s",
            [filter_status, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM vehicles ORDER BY vehicle_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/vehicles/{vehicle_id}", response_model=Vehicle, summary="Get vehicle details by ID")
def get_vehicle(vehicle_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single vehicle."""
    row = db.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", [vehicle_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle {vehicle_id} not found")
    return serialize_row(row)


@router.post("/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED, summary="Register a vehicle")
def create_vehicle(data: VehicleInput, db: Database) -> dict[str, Any]:
    """Register a new fleet vehicle with server-assigned ID (VEH-xxxx)."""
    new_id = generate_next_id(db, "vehicles", "vehicle_id", "VEH-")
    db.execute(
        """
        INSERT INTO vehicles (vehicle_id, vehicle_type, plate_number, driver, status, daily_operating_cost)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.vehicle_type, data.plate_number, data.driver, data.status, data.daily_operating_cost],
    )
    return {**data.model_dump(), "vehicle_id": new_id}


@router.patch("/vehicles/{vehicle_id}", response_model=Vehicle, summary="Partially update vehicle details")
def update_vehicle(vehicle_id: str, data: PartialVehicleInput, db: Database) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", [vehicle_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle {vehicle_id} not found")

    merged = {
        "vehicle_type": data.vehicle_type if data.vehicle_type is not None else existing["vehicle_type"],
        "plate_number": data.plate_number if data.plate_number is not None else existing["plate_number"],
        "driver": data.driver if data.driver is not None else existing["driver"],
        "status": data.status if data.status is not None else existing["status"],
        "daily_operating_cost": data.daily_operating_cost if data.daily_operating_cost is not None else existing["daily_operating_cost"],
    }
    db.execute(
        """
        UPDATE vehicles
        SET vehicle_type = %s, plate_number = %s, driver = %s, status = %s, daily_operating_cost = %s
        WHERE vehicle_id = %s
        """,
        [merged["vehicle_type"], merged["plate_number"], merged["driver"], merged["status"], merged["daily_operating_cost"], vehicle_id],
    )
    return {**merged, "vehicle_id": vehicle_id}


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete vehicle")
def delete_vehicle(vehicle_id: str, db: Database) -> None:
    """Delete a vehicle asset."""
    res = db.execute("DELETE FROM vehicles WHERE vehicle_id = %s", [vehicle_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle {vehicle_id} not found")


# ==========================================================================
# 3. Maintenance Scheduling
# (Auto-sets equipment status to 'Under Maintenance')
# ==========================================================================
@router.get("/maintenance-records", response_model=list[MaintenanceRecord], summary="List maintenance records")
@router.get("/maintenance", response_model=list[MaintenanceRecord], summary="List maintenance records (alias)")
def list_maintenance_records(
    db: Database,
    equipment_id: str | None = Query(None, description="Filter by equipment ID"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List equipment maintenance logs and downtime records."""
    if equipment_id:
        rows = db.execute(
            "SELECT * FROM maintenance_records WHERE equipment_id = %s ORDER BY maintenance_id LIMIT %s",
            [equipment_id, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM maintenance_records ORDER BY maintenance_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/maintenance-records/{maintenance_id}", response_model=MaintenanceRecord, summary="Get maintenance record by ID")
@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceRecord, summary="Get maintenance record by ID (alias)")
def get_maintenance_record(maintenance_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single maintenance record."""
    row = db.execute("SELECT * FROM maintenance_records WHERE maintenance_id = %s", [maintenance_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Maintenance record {maintenance_id} not found")
    return serialize_row(row)


@router.post("/maintenance-records", response_model=MaintenanceRecord, status_code=status.HTTP_201_CREATED, summary="Schedule maintenance")
@router.post("/maintenance", response_model=MaintenanceRecord, status_code=status.HTTP_201_CREATED, summary="Schedule maintenance (alias)")
def create_maintenance_record(data: MaintenanceRecordInput, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Registers a maintenance record. If status is Scheduled or In Progress,
    automatically updates the equipment status to 'Under Maintenance'.
    """
    if not db.execute("SELECT 1 FROM equipment WHERE equipment_id = %s", [data.equipment_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {data.equipment_id} not found")

    new_id = generate_next_id(db, "maintenance_records", "maintenance_id", "MNT-")
    db.execute(
        """
        INSERT INTO maintenance_records (maintenance_id, equipment_id, maintenance_date, maintenance_type, maintenance_cost, duration_days, maintenance_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.equipment_id, data.maintenance_date, data.maintenance_type, data.maintenance_cost, data.duration_days, data.maintenance_status],
    )
    # Auto-sets equipment status to 'Under Maintenance'
    if data.maintenance_status in ("Scheduled", "In Progress"):
        db.execute("UPDATE equipment SET status = 'Under Maintenance' WHERE equipment_id = %s", [data.equipment_id])

    return {**data.model_dump(), "maintenance_id": new_id}


@router.delete("/maintenance-records/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete maintenance record")
@router.delete("/maintenance/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete maintenance record (alias)")
def delete_maintenance_record(maintenance_id: str, db: Database) -> None:
    """Delete a maintenance log record and release equipment if no other active maintenance exists."""
    existing = db.execute("SELECT equipment_id FROM maintenance_records WHERE maintenance_id = %s", [maintenance_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Maintenance record {maintenance_id} not found")

    eq_id = existing["equipment_id"]
    db.execute("DELETE FROM maintenance_records WHERE maintenance_id = %s", [maintenance_id])

    # Check if there are other scheduled/in-progress maintenance records for this equipment
    other = db.execute(
        "SELECT 1 FROM maintenance_records WHERE equipment_id = %s AND maintenance_status IN ('Scheduled', 'In Progress')",
        [eq_id],
    ).fetchone()
    if not other:
        # Revert equipment to Available if no other active maintenance
        db.execute("UPDATE equipment SET status = 'Available' WHERE equipment_id = %s AND status = 'Under Maintenance'", [eq_id])


# ==========================================================================
# 4. Equipment Allocations (with conflict checking)
# ==========================================================================
@router.get("/equipment-allocations", response_model=list[EquipmentAllocation], summary="List equipment allocations")
def list_equipment_allocations(
    db: Database,
    project_id: str | None = Query(None, description="Filter by project ID"),
    equipment_id: str | None = Query(None, description="Filter by equipment ID"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List equipment project bookings."""
    query = "SELECT * FROM equipment_allocations WHERE 1=1"
    params: list[Any] = []
    if project_id:
        query += " AND project_id = %s"
        params.append(project_id)
    if equipment_id:
        query += " AND equipment_id = %s"
        params.append(equipment_id)
    query += " ORDER BY allocation_id LIMIT %s"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/equipment-allocations/{allocation_id}", response_model=EquipmentAllocation, summary="Get equipment allocation by ID")
def get_equipment_allocation(allocation_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single equipment allocation."""
    row = db.execute("SELECT * FROM equipment_allocations WHERE allocation_id = %s", [allocation_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {allocation_id} not found")
    return serialize_row(row)


@router.post("/equipment-allocations", response_model=EquipmentAllocation, status_code=status.HTTP_201_CREATED, summary="Create equipment allocation with overlap check")
def create_equipment_allocation(data: EquipmentAllocationInput, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Creates an equipment project booking with automatic date overlap validation.
    Returns HTTP 409 Conflict if the asset is already booked during the requested date range.
    """
    if data.start_date > data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [data.project_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found")
    if not db.execute("SELECT 1 FROM equipment WHERE equipment_id = %s", [data.equipment_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {data.equipment_id} not found")

    conflict = db.execute(
        """
        SELECT allocation_id, project_id FROM equipment_allocations
        WHERE equipment_id = %s
          AND allocation_status NOT IN ('Completed', 'Cancelled')
          AND start_date <= %s
          AND end_date >= %s
        """,
        [data.equipment_id, data.end_date, data.start_date],
    ).fetchone()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking Conflict: Equipment {data.equipment_id} is already booked by {conflict['project_id']} ({conflict['allocation_id']}) in this period.",
        )

    new_id = generate_next_id(db, "equipment_allocations", "allocation_id", "EA-")
    db.execute(
        """
        INSERT INTO equipment_allocations (allocation_id, project_id, equipment_id, start_date, end_date, purpose, allocation_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.project_id, data.equipment_id, data.start_date, data.end_date, data.purpose, data.allocation_status],
    )
    return {**data.model_dump(), "allocation_id": new_id}


@router.patch("/equipment-allocations/{allocation_id}", summary="Reschedule or reassign equipment allocation")
def update_equipment_allocation(allocation_id: str, data: PartialEquipmentAllocationInput, db: Database) -> dict[str, Any]:
    """Reschedule or reassign an equipment allocation with date overlap validation."""
    existing = db.execute("SELECT * FROM equipment_allocations WHERE allocation_id = %s", [allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {allocation_id} not found")

    new_eq = data.equipment_id if data.equipment_id is not None else existing["equipment_id"]
    new_start = data.start_date if data.start_date is not None else existing["start_date"]
    new_end = data.end_date if data.end_date is not None else existing["end_date"]
    new_status = data.allocation_status if data.allocation_status is not None else existing["allocation_status"]
    new_purpose = data.purpose if data.purpose is not None else existing["purpose"]
    new_project = data.project_id if data.project_id is not None else existing["project_id"]

    if new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if new_status not in ("Completed", "Cancelled"):
        conflict = db.execute(
            """
            SELECT allocation_id, project_id FROM equipment_allocations
            WHERE equipment_id = %s
              AND allocation_id != %s
              AND allocation_status NOT IN ('Completed', 'Cancelled')
              AND start_date <= %s
              AND end_date >= %s
            """,
            [new_eq, allocation_id, new_end, new_start],
        ).fetchone()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Equipment {new_eq} is already booked by {conflict['project_id']} ({conflict['allocation_id']}).",
            )

    db.execute(
        """
        UPDATE equipment_allocations
        SET project_id = %s, equipment_id = %s, start_date = %s, end_date = %s, purpose = %s, allocation_status = %s
        WHERE allocation_id = %s
        """,
        [new_project, new_eq, new_start, new_end, new_purpose, new_status, allocation_id],
    )
    if new_status == "Cancelled":
        db.execute("UPDATE equipment SET status = 'Available' WHERE equipment_id = %s", [existing["equipment_id"]])

    updated = db.execute("SELECT * FROM equipment_allocations WHERE allocation_id = %s", [allocation_id]).fetchone()
    return serialize_row(updated)


@router.patch("/equipment-allocations/{allocation_id}/status", summary="Update equipment allocation status")
def update_equipment_allocation_status(allocation_id: str, body: AllocationStatusUpdate, db: Database) -> dict[str, Any]:
    """Change allocation status (Scheduled, Active, Completed, Cancelled). Validates allocation exists first."""
    existing = db.execute("SELECT * FROM equipment_allocations WHERE allocation_id = %s", [allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {allocation_id} not found")

    db.execute(
        "UPDATE equipment_allocations SET allocation_status = %s WHERE allocation_id = %s",
        [body.allocation_status, allocation_id],
    )
    if body.allocation_status == "Cancelled":
        db.execute("UPDATE equipment SET status = 'Available' WHERE equipment_id = %s", [existing["equipment_id"]])
    return {"allocation_id": allocation_id, "allocation_status": body.allocation_status}


@router.delete("/equipment-allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete equipment allocation")
def delete_equipment_allocation(allocation_id: str, db: Database) -> None:
    """Delete an equipment allocation record."""
    res = db.execute("DELETE FROM equipment_allocations WHERE allocation_id = %s", [allocation_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {allocation_id} not found")


# ==========================================================================
# 5. Vehicle Allocations (with conflict checking)
# ==========================================================================
@router.get("/vehicle-allocations", response_model=list[VehicleAllocation], summary="List vehicle allocations")
def list_vehicle_allocations(
    db: Database,
    project_id: str | None = Query(None, description="Filter by project ID"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List vehicle project allocations."""
    if project_id:
        rows = db.execute(
            "SELECT * FROM vehicle_allocations WHERE project_id = %s ORDER BY vehicle_allocation_id LIMIT %s",
            [project_id, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM vehicle_allocations ORDER BY vehicle_allocation_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/vehicle-allocations/{vehicle_allocation_id}", response_model=VehicleAllocation, summary="Get vehicle allocation by ID")
def get_vehicle_allocation(vehicle_allocation_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single vehicle allocation."""
    row = db.execute("SELECT * FROM vehicle_allocations WHERE vehicle_allocation_id = %s", [vehicle_allocation_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {vehicle_allocation_id} not found")
    return serialize_row(row)


@router.post("/vehicle-allocations", response_model=VehicleAllocation, status_code=status.HTTP_201_CREATED, summary="Create vehicle allocation")
def create_vehicle_allocation(data: VehicleAllocationInput, db: Database) -> dict[str, Any]:
    """Create vehicle allocation with date overlap conflict prevention."""
    if data.start_date > data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [data.project_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found")
    if not db.execute("SELECT 1 FROM vehicles WHERE vehicle_id = %s", [data.vehicle_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle {data.vehicle_id} not found")

    conflict = db.execute(
        """
        SELECT vehicle_allocation_id, project_id FROM vehicle_allocations
        WHERE vehicle_id = %s
          AND allocation_status NOT IN ('Completed', 'Cancelled')
          AND start_date <= %s
          AND end_date >= %s
        """,
        [data.vehicle_id, data.end_date, data.start_date],
    ).fetchone()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: Vehicle {data.vehicle_id} is already allocated to {conflict['project_id']} ({conflict['vehicle_allocation_id']}) in this period.",
        )

    new_id = generate_next_id(db, "vehicle_allocations", "vehicle_allocation_id", "VA-")
    db.execute(
        """
        INSERT INTO vehicle_allocations (vehicle_allocation_id, project_id, vehicle_id, start_date, end_date, purpose, allocation_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.project_id, data.vehicle_id, data.start_date, data.end_date, data.purpose, data.allocation_status],
    )
    return {**data.model_dump(), "vehicle_allocation_id": new_id}


@router.patch("/vehicle-allocations/{vehicle_allocation_id}", summary="Reschedule or reassign vehicle allocation")
def update_vehicle_allocation(vehicle_allocation_id: str, data: PartialVehicleAllocationInput, db: Database) -> dict[str, Any]:
    """Reschedule or reassign a vehicle allocation with date overlap validation."""
    existing = db.execute("SELECT * FROM vehicle_allocations WHERE vehicle_allocation_id = %s", [vehicle_allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {vehicle_allocation_id} not found")

    new_veh = data.vehicle_id if data.vehicle_id is not None else existing["vehicle_id"]
    new_start = data.start_date if data.start_date is not None else existing["start_date"]
    new_end = data.end_date if data.end_date is not None else existing["end_date"]
    new_status = data.allocation_status if data.allocation_status is not None else existing["allocation_status"]
    new_purpose = data.purpose if data.purpose is not None else existing["purpose"]
    new_project = data.project_id if data.project_id is not None else existing["project_id"]

    if new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if new_status not in ("Completed", "Cancelled"):
        conflict = db.execute(
            """
            SELECT vehicle_allocation_id, project_id FROM vehicle_allocations
            WHERE vehicle_id = %s
              AND vehicle_allocation_id != %s
              AND allocation_status NOT IN ('Completed', 'Cancelled')
              AND start_date <= %s
              AND end_date >= %s
            """,
            [new_veh, vehicle_allocation_id, new_end, new_start],
        ).fetchone()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Vehicle {new_veh} is already allocated to {conflict['project_id']} ({conflict['vehicle_allocation_id']}).",
            )

    db.execute(
        """
        UPDATE vehicle_allocations
        SET project_id = %s, vehicle_id = %s, start_date = %s, end_date = %s, purpose = %s, allocation_status = %s
        WHERE vehicle_allocation_id = %s
        """,
        [new_project, new_veh, new_start, new_end, new_purpose, new_status, vehicle_allocation_id],
    )
    if new_status == "Cancelled":
        db.execute("UPDATE vehicles SET status = 'Available' WHERE vehicle_id = %s", [existing["vehicle_id"]])

    updated = db.execute("SELECT * FROM vehicle_allocations WHERE vehicle_allocation_id = %s", [vehicle_allocation_id]).fetchone()
    return serialize_row(updated)


@router.patch("/vehicle-allocations/{vehicle_allocation_id}/status", summary="Update vehicle allocation status")
def update_vehicle_allocation_status(vehicle_allocation_id: str, body: AllocationStatusUpdate, db: Database) -> dict[str, Any]:
    """Change vehicle allocation status. Validates allocation exists first."""
    existing = db.execute("SELECT * FROM vehicle_allocations WHERE vehicle_allocation_id = %s", [vehicle_allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {vehicle_allocation_id} not found")

    db.execute(
        "UPDATE vehicle_allocations SET allocation_status = %s WHERE vehicle_allocation_id = %s",
        [body.allocation_status, vehicle_allocation_id],
    )
    if body.allocation_status == "Cancelled":
        db.execute("UPDATE vehicles SET status = 'Available' WHERE vehicle_id = %s", [existing["vehicle_id"]])
    return {"vehicle_allocation_id": vehicle_allocation_id, "allocation_status": body.allocation_status}


@router.delete("/vehicle-allocations/{vehicle_allocation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete vehicle allocation")
def delete_vehicle_allocation(vehicle_allocation_id: str, db: Database) -> None:
    """Delete a vehicle allocation record."""
    res = db.execute("DELETE FROM vehicle_allocations WHERE vehicle_allocation_id = %s", [vehicle_allocation_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {vehicle_allocation_id} not found")
