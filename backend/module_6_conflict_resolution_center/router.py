"""
Module 6: Resource Conflict Resolution Center Router
=====================================================
The central cross-cutting operational engine of BuildSync:
- Detects overlapping date ranges for physical resources across projects
  (Equipment, Workforce, and Fleet Vehicles).
- Overlap rule: (a.start <= b.end) AND (a.end >= b.start).
- Provides resolution action endpoints (Cancel, Reschedule, Reassign).

Endpoints:
- Detection: GET /conflicts/equipment, GET /conflicts/employees, GET /conflicts/vehicles, GET /conflicts/summary
- Actions: POST /conflicts/resolve/cancel, POST /conflicts/resolve/reschedule, POST /conflicts/resolve/reassign
"""

from typing import Any
from fastapi import APIRouter, HTTPException, status

from app.database import Database, serialize_row
from .models import (
    CancelAllocationInput,
    ConflictSummary,
    ReassignInput,
    RescheduleInput,
    ResolutionResult,
)

router = APIRouter(prefix="/conflicts", tags=["Module 6: Resource Conflict Resolution Center"])


# ==========================================================================
# 1. Conflict Detection Endpoints
# ==========================================================================
@router.get("/equipment", summary="Detect equipment date-overlap conflicts")
def equipment_conflicts(db: Database) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Surfaces all pairs of equipment allocations where the same physical machine
    is double-booked across concurrent projects with overlapping date ranges.
    Overlap condition: (a.start <= b.end) AND (a.end >= b.start).
    """
    rows = db.execute(
        """
        SELECT
            a.allocation_id   AS allocation_a,
            b.allocation_id   AS allocation_b,
            a.equipment_id,
            eq.name           AS equipment_name,
            a.project_id      AS project_a,
            b.project_id      AS project_b,
            a.start_date      AS a_start,
            a.end_date        AS a_end,
            b.start_date      AS b_start,
            b.end_date        AS b_end
        FROM equipment_allocations a
        JOIN equipment_allocations b
            ON  a.equipment_id = b.equipment_id
            AND a.allocation_id < b.allocation_id
            AND a.allocation_status NOT IN ('Completed', 'Cancelled')
            AND b.allocation_status NOT IN ('Completed', 'Cancelled')
            AND a.start_date <= b.end_date
            AND a.end_date   >= b.start_date
        JOIN equipment eq ON eq.equipment_id = a.equipment_id
        ORDER BY a.equipment_id, a.start_date
        """
    ).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/employees", summary="Detect employee date-overlap conflicts")
def employee_conflicts(db: Database) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Surfaces all pairs of employee allocations where the same worker is
    simultaneously booked on two concurrent projects.
    """
    rows = db.execute(
        """
        SELECT
            a.employee_allocation_id AS allocation_a,
            b.employee_allocation_id AS allocation_b,
            a.employee_id,
            e.name                   AS employee_name,
            a.project_id             AS project_a,
            b.project_id             AS project_b,
            a.start_date             AS a_start,
            a.end_date               AS a_end,
            b.start_date             AS b_start,
            b.end_date               AS b_end
        FROM employee_allocations a
        JOIN employee_allocations b
            ON  a.employee_id = b.employee_id
            AND a.employee_allocation_id < b.employee_allocation_id
            AND a.allocation_status NOT IN ('Completed', 'Cancelled')
            AND b.allocation_status NOT IN ('Completed', 'Cancelled')
            AND a.start_date <= b.end_date
            AND a.end_date   >= b.start_date
        JOIN employees e ON e.employee_id = a.employee_id
        ORDER BY a.employee_id, a.start_date
        """
    ).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/vehicles", summary="Detect vehicle date-overlap conflicts")
def vehicle_conflicts(db: Database) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Surfaces all pairs of vehicle allocations where the same fleet vehicle
    is double-booked across concurrent projects.
    """
    rows = db.execute(
        """
        SELECT
            a.vehicle_allocation_id AS allocation_a,
            b.vehicle_allocation_id AS allocation_b,
            a.vehicle_id,
            v.plate_number          AS vehicle_plate,
            v.vehicle_type          AS vehicle_type,
            a.project_id            AS project_a,
            b.project_id            AS project_b,
            a.start_date            AS a_start,
            a.end_date              AS a_end,
            b.start_date            AS b_start,
            b.end_date              AS b_end
        FROM vehicle_allocations a
        JOIN vehicle_allocations b
            ON  a.vehicle_id = b.vehicle_id
            AND a.vehicle_allocation_id < b.vehicle_allocation_id
            AND a.allocation_status NOT IN ('Completed', 'Cancelled')
            AND b.allocation_status NOT IN ('Completed', 'Cancelled')
            AND a.start_date <= b.end_date
            AND a.end_date   >= b.start_date
        JOIN vehicles v ON v.vehicle_id = a.vehicle_id
        ORDER BY a.vehicle_id, a.start_date
        """
    ).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/summary", response_model=ConflictSummary, summary="Conflict summary KPI counts for UI badges")
def conflicts_summary(db: Database) -> dict[str, Any]:
    """
    Summary badge counters (Equipment, Workforce, Vehicles, Total) for the Conflict Center header.
    Uses efficient COUNT-based SQL for fast dashboard rendering.
    """
    row = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM (
                SELECT 1 FROM equipment_allocations a
                JOIN equipment_allocations b
                    ON a.equipment_id = b.equipment_id
                    AND a.allocation_id < b.allocation_id
                    AND a.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND b.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND a.start_date <= b.end_date
                    AND a.end_date >= b.start_date
            ) eq_conflicts) AS equipment,
            (SELECT COUNT(*) FROM (
                SELECT 1 FROM employee_allocations a
                JOIN employee_allocations b
                    ON a.employee_id = b.employee_id
                    AND a.employee_allocation_id < b.employee_allocation_id
                    AND a.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND b.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND a.start_date <= b.end_date
                    AND a.end_date >= b.start_date
            ) emp_conflicts) AS employees,
            (SELECT COUNT(*) FROM (
                SELECT 1 FROM vehicle_allocations a
                JOIN vehicle_allocations b
                    ON a.vehicle_id = b.vehicle_id
                    AND a.vehicle_allocation_id < b.vehicle_allocation_id
                    AND a.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND b.allocation_status NOT IN ('Completed', 'Cancelled')
                    AND a.start_date <= b.end_date
                    AND a.end_date >= b.start_date
            ) veh_conflicts) AS vehicles
        """
    ).fetchone()

    eq_count = int(row["equipment"] or 0)
    emp_count = int(row["employees"] or 0)
    veh_count = int(row["vehicles"] or 0)
    return {
        "equipment": eq_count,
        "employees": emp_count,
        "vehicles": veh_count,
        "total": eq_count + emp_count + veh_count,
    }


# ==========================================================================
# 2. Conflict Resolution Actions
# ==========================================================================
_ALLOCATION_CONFIG = {
    "equipment": {
        "table": "equipment_allocations",
        "id_col": "allocation_id",
        "resource_col": "equipment_id",
        "resource_table": "equipment",
    },
    "employee": {
        "table": "employee_allocations",
        "id_col": "employee_allocation_id",
        "resource_col": "employee_id",
        "resource_table": "employees",
    },
    "vehicle": {
        "table": "vehicle_allocations",
        "id_col": "vehicle_allocation_id",
        "resource_col": "vehicle_id",
        "resource_table": "vehicles",
    },
}


def _get_config(allocation_type: str) -> dict[str, str]:
    """Look up the SQL table/column config for a given allocation type, or raise 400."""
    atype = allocation_type.lower()
    config = _ALLOCATION_CONFIG.get(atype)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid allocation_type '{allocation_type}'. Must be 'equipment', 'employee', or 'vehicle'.",
        )
    return config


@router.post("/resolve/cancel", response_model=ResolutionResult, summary="Conflict Resolution: Cancel booking")
def resolve_conflict_cancel(data: CancelAllocationInput, db: Database) -> dict[str, Any]:
    """
    Conflict Resolution Action 1:
    Cancels one of the conflicting allocation records to immediately free the resource.
    Releases equipment/vehicle back to 'Available' status.
    """
    config = _get_config(data.allocation_type)
    table, id_col, resource_col = config["table"], config["id_col"], config["resource_col"]

    existing = db.execute(f"SELECT * FROM {table} WHERE {id_col} = %s", [data.allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {data.allocation_id} not found.")

    res = db.execute(
        f"UPDATE {table} SET allocation_status = 'Cancelled' WHERE {id_col} = %s",
        [data.allocation_id],
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {data.allocation_id} not found.")

    # Auto-release resource if it's equipment or vehicle
    atype = data.allocation_type.lower()
    if atype == "equipment":
        db.execute("UPDATE equipment SET status = 'Available' WHERE equipment_id = %s", [existing[resource_col]])
    elif atype == "vehicle":
        db.execute("UPDATE vehicles SET status = 'Available' WHERE vehicle_id = %s", [existing[resource_col]])

    return {
        "status": "resolved",
        "action": "cancelled",
        "allocation_id": data.allocation_id,
        "allocation_type": atype,
    }


@router.post("/resolve/reschedule", summary="Conflict Resolution: Reschedule dates")
def resolve_conflict_reschedule(data: RescheduleInput, db: Database) -> dict[str, Any]:
    """
    Conflict Resolution Action 2:
    Updates start_date and end_date on an allocation so it no longer overlaps.
    Validates that the new dates don't create a new conflict with another allocation.
    """
    if data.new_start_date > data.new_end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new_start_date must be before or equal to new_end_date.")

    config = _get_config(data.allocation_type)
    table, id_col, resource_col = config["table"], config["id_col"], config["resource_col"]

    existing = db.execute(
        f"SELECT * FROM {table} WHERE {id_col} = %s", [data.allocation_id]
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {data.allocation_id} not found.")

    resource_id = existing[resource_col]

    # Check the new dates don't create another overlap
    conflict = db.execute(
        f"""
        SELECT {id_col} FROM {table}
        WHERE {resource_col} = %s
          AND {id_col} != %s
          AND allocation_status NOT IN ('Completed', 'Cancelled')
          AND start_date <= %s
          AND end_date >= %s
        """,
        [resource_id, data.allocation_id, data.new_end_date, data.new_start_date],
    ).fetchone()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reschedule: new dates still overlap with allocation {conflict[id_col]}.",
        )

    db.execute(
        f"UPDATE {table} SET start_date = %s, end_date = %s WHERE {id_col} = %s",
        [data.new_start_date, data.new_end_date, data.allocation_id],
    )

    return {
        "status": "resolved",
        "action": "rescheduled",
        "allocation_id": data.allocation_id,
        "allocation_type": data.allocation_type.lower(),
        "new_start_date": data.new_start_date.isoformat(),
        "new_end_date": data.new_end_date.isoformat(),
    }


@router.post("/resolve/reassign", summary="Conflict Resolution: Reassign to replacement resource")
def resolve_conflict_reassign(data: ReassignInput, db: Database) -> dict[str, Any]:
    """
    Conflict Resolution Action 3:
    Reassigns an allocation to a different available resource.
    Validates the replacement resource exists and isn't already double-booked.
    """
    config = _get_config(data.allocation_type)
    table, id_col, resource_col, resource_table = (
        config["table"], config["id_col"], config["resource_col"], config["resource_table"]
    )

    # Validate replacement resource exists
    if not db.execute(f"SELECT 1 FROM {resource_table} WHERE {resource_col} = %s", [data.new_resource_id]).fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replacement {data.allocation_type} {data.new_resource_id} not found.",
        )

    existing = db.execute(
        f"SELECT * FROM {table} WHERE {id_col} = %s", [data.allocation_id]
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {data.allocation_id} not found.")

    # Check the replacement resource isn't also double-booked in this date range
    conflict = db.execute(
        f"""
        SELECT {id_col} FROM {table}
        WHERE {resource_col} = %s
          AND {id_col} != %s
          AND allocation_status NOT IN ('Completed', 'Cancelled')
          AND start_date <= %s
          AND end_date >= %s
        """,
        [data.new_resource_id, data.allocation_id, existing["end_date"], existing["start_date"]],
    ).fetchone()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reassign: replacement {data.allocation_type} {data.new_resource_id} is already booked by {conflict[id_col]}.",
        )

    db.execute(
        f"UPDATE {table} SET {resource_col} = %s WHERE {id_col} = %s",
        [data.new_resource_id, data.allocation_id],
    )

    return {
        "status": "resolved",
        "action": "reassigned",
        "allocation_id": data.allocation_id,
        "allocation_type": data.allocation_type.lower(),
        "new_resource_id": data.new_resource_id,
    }
