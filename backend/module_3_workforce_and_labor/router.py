"""
Module 3: Workforce & Labor Management Router
=============================================
Manages employees, subcontracted third-party labor,
project employee allocations, and worker availability matching.

Endpoints:
- Employees: GET /employees, GET /employees/{id}, POST, PATCH, DELETE
- Contractors: GET /contractors, GET /contractors/{id}, POST, PATCH, DELETE
- Allocations: GET /employee-allocations, POST (with conflict check), PATCH, PATCH status, DELETE
- Complex: GET /employees/available/search?start_date=...&end_date=...&skill=...
"""

from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_roles
from app.database import Database, generate_next_id, serialize_row
from .models import (
    AllocationStatusUpdate,
    Contractor,
    ContractorInput,
    Employee,
    EmployeeAllocation,
    EmployeeAllocationInput,
    EmployeeInput,
    PartialContractorInput,
    PartialEmployeeAllocationInput,
    PartialEmployeeInput,
)

router = APIRouter(tags=["Module 3: Workforce & Labor Management"])


# ==========================================================================
# 1. Employees Management
# ==========================================================================
@router.get("/employees", response_model=list[Employee], summary="List all employees")
def list_employees(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Filter by employment status (Active, Inactive, On Leave)"),
    skill: str | None = Query(None, description="Filter by skill or trade (case-insensitive substring)"),
    limit: int = Query(600, ge=1, le=600),
    _: dict[str, Any] = Depends(require_roles("admin", "employee")),
) -> list[dict[str, Any]]:
    """List in-house employees with optional status and skill filtering."""
    query = "SELECT * FROM employees WHERE 1=1"
    params: list[Any] = []
    if filter_status:
        query += " AND employment_status = %s"
        params.append(filter_status)
    if skill:
        query += " AND skill ILIKE %s"
        params.append(f"%{skill}%")
    query += " ORDER BY employee_id LIMIT %s"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    return [serialize_row(r) for r in rows]


# ── IMPORTANT: Static route BEFORE parameterized /{employee_id} to prevent path masking ──
@router.get("/employees/available/search", summary="Search available employees for date range and skill")
def get_available_employees(
    db: Database,
    start_date: date = Query(..., description="Desired booking start date"),
    end_date: date = Query(..., description="Desired booking end date"),
    skill: str | None = Query(None, description="Optional required skill or trade"),
) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Returns active employees who have NO conflicting active/scheduled allocations
    within the specified date window, optionally filtered by required trade skill.
    """
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    query = """
        SELECT e.*
        FROM employees e
        WHERE e.employment_status = 'Active'
          AND NOT EXISTS (
              SELECT 1 FROM employee_allocations ea
              WHERE ea.employee_id = e.employee_id
                AND ea.allocation_status NOT IN ('Completed', 'Cancelled')
                AND ea.start_date <= %s
                AND ea.end_date >= %s
          )
    """
    params: list[Any] = [end_date, start_date]
    if skill:
        query += " AND e.skill ILIKE %s"
        params.append(f"%{skill}%")
    query += " ORDER BY e.name LIMIT 50"
    rows = db.execute(query, params).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/employees/{employee_id}", response_model=Employee, summary="Get employee details by ID")
def get_employee(employee_id: str, db: Database, _: dict[str, Any] = Depends(require_roles("admin", "employee"))) -> dict[str, Any]:
    """Retrieve details for a single employee."""
    row = db.execute("SELECT * FROM employees WHERE employee_id = %s", [employee_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {employee_id} not found")
    return serialize_row(row)


@router.post("/employees", response_model=Employee, status_code=status.HTTP_201_CREATED, summary="Create an employee")
def create_employee(data: EmployeeInput, db: Database, _: dict[str, Any] = Depends(require_roles("admin"))) -> dict[str, Any]:
    """Register a new in-house employee with server-assigned ID (EMP-xxxx)."""
    new_id = generate_next_id(db, "employees", "employee_id", "EMP-")
    db.execute(
        """
        INSERT INTO employees (employee_id, name, position, skill, phone, employment_status, daily_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.name, data.position, data.skill, data.phone, data.employment_status, data.daily_rate],
    )
    return {**data.model_dump(), "employee_id": new_id}


@router.patch("/employees/{employee_id}", response_model=Employee, summary="Partially update employee details")
def update_employee(employee_id: str, data: PartialEmployeeInput, db: Database, _: dict[str, Any] = Depends(require_roles("admin"))) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM employees WHERE employee_id = %s", [employee_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {employee_id} not found")

    merged = {
        "name": data.name if data.name is not None else existing["name"],
        "position": data.position if data.position is not None else existing["position"],
        "skill": data.skill if data.skill is not None else existing["skill"],
        "phone": data.phone if data.phone is not None else existing["phone"],
        "employment_status": data.employment_status if data.employment_status is not None else existing["employment_status"],
        "daily_rate": data.daily_rate if data.daily_rate is not None else existing["daily_rate"],
    }
    db.execute(
        """
        UPDATE employees
        SET name = %s, position = %s, skill = %s, phone = %s, employment_status = %s, daily_rate = %s
        WHERE employee_id = %s
        """,
        [merged["name"], merged["position"], merged["skill"], merged["phone"], merged["employment_status"], merged["daily_rate"], employee_id],
    )
    return {**merged, "employee_id": employee_id}


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an employee")
def delete_employee(employee_id: str, db: Database, _: dict[str, Any] = Depends(require_roles("admin"))) -> None:
    """Delete an employee and their corresponding allocation records."""
    res = db.execute("DELETE FROM employees WHERE employee_id = %s", [employee_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {employee_id} not found")


# ==========================================================================
# 2. Contractors Management
# ==========================================================================
@router.get("/contractors", response_model=list[Contractor], summary="List all contractors")
def list_contractors(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Active, Inactive"),
    limit: int = Query(600, ge=1, le=600),
) -> list[dict[str, Any]]:
    """List third-party external contractors and specialized firms."""
    if filter_status:
        rows = db.execute(
            "SELECT * FROM contractors WHERE status = %s ORDER BY contractor_id LIMIT %s",
            [filter_status, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM contractors ORDER BY contractor_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/contractors/{contractor_id}", response_model=Contractor, summary="Get contractor details by ID")
def get_contractor(contractor_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single contractor."""
    row = db.execute("SELECT * FROM contractors WHERE contractor_id = %s", [contractor_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contractor {contractor_id} not found")
    return serialize_row(row)


@router.post("/contractors", response_model=Contractor, status_code=status.HTTP_201_CREATED, summary="Create a contractor")
def create_contractor(data: ContractorInput, db: Database) -> dict[str, Any]:
    """Register a new third-party contractor firm with server-assigned ID (CON-xxxx)."""
    new_id = generate_next_id(db, "contractors", "contractor_id", "CON-")
    db.execute(
        """
        INSERT INTO contractors (contractor_id, contractor_name, specialization, contact_person, phone, rating, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.contractor_name, data.specialization, data.contact_person, data.phone, data.rating, data.status],
    )
    return {**data.model_dump(), "contractor_id": new_id}


@router.patch("/contractors/{contractor_id}", response_model=Contractor, summary="Partially update contractor details")
def update_contractor(contractor_id: str, data: PartialContractorInput, db: Database) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM contractors WHERE contractor_id = %s", [contractor_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contractor {contractor_id} not found")

    merged = {
        "contractor_name": data.contractor_name if data.contractor_name is not None else existing["contractor_name"],
        "specialization": data.specialization if data.specialization is not None else existing["specialization"],
        "contact_person": data.contact_person if data.contact_person is not None else existing["contact_person"],
        "phone": data.phone if data.phone is not None else existing["phone"],
        "rating": data.rating if data.rating is not None else existing["rating"],
        "status": data.status if data.status is not None else existing["status"],
    }
    db.execute(
        """
        UPDATE contractors
        SET contractor_name = %s, specialization = %s, contact_person = %s, phone = %s, rating = %s, status = %s
        WHERE contractor_id = %s
        """,
        [merged["contractor_name"], merged["specialization"], merged["contact_person"], merged["phone"], merged["rating"], merged["status"], contractor_id],
    )
    return {**merged, "contractor_id": contractor_id}


@router.delete("/contractors/{contractor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete contractor")
def delete_contractor(contractor_id: str, db: Database) -> None:
    """Delete a contractor firm record."""
    res = db.execute("DELETE FROM contractors WHERE contractor_id = %s", [contractor_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contractor {contractor_id} not found")


# ==========================================================================
# 3. Employee Allocation & Scheduling
# ==========================================================================
@router.get("/employee-allocations", response_model=list[EmployeeAllocation], summary="List employee allocations")
def list_employee_allocations(
    db: Database,
    project_id: str | None = Query(None, description="Filter by project ID"),
    employee_id: str | None = Query(None, description="Filter by employee ID"),
    limit: int = Query(600, ge=1, le=600),
) -> list[dict[str, Any]]:
    """List worker project assignments."""
    query = "SELECT * FROM employee_allocations WHERE 1=1"
    params: list[Any] = []
    if project_id:
        query += " AND project_id = %s"
        params.append(project_id)
    if employee_id:
        query += " AND employee_id = %s"
        params.append(employee_id)
    query += " ORDER BY employee_allocation_id LIMIT %s"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/employee-allocations/{employee_allocation_id}", response_model=EmployeeAllocation, summary="Get employee allocation by ID")
def get_employee_allocation(employee_allocation_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single employee assignment."""
    row = db.execute("SELECT * FROM employee_allocations WHERE employee_allocation_id = %s", [employee_allocation_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {employee_allocation_id} not found")
    return serialize_row(row)


@router.post("/employee-allocations", response_model=EmployeeAllocation, status_code=status.HTTP_201_CREATED, summary="Create employee allocation with overlap check")
def create_employee_allocation(data: EmployeeAllocationInput, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Assigns an employee to a project with automatic double-booking prevention.
    Returns HTTP 409 Conflict if the worker is already booked in that date range.
    """
    if data.start_date > data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [data.project_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found")
    if not db.execute("SELECT 1 FROM employees WHERE employee_id = %s", [data.employee_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {data.employee_id} not found")

    conflict = db.execute(
        """
        SELECT employee_allocation_id, project_id FROM employee_allocations
        WHERE employee_id = %s
          AND allocation_status NOT IN ('Completed', 'Cancelled')
          AND start_date <= %s
          AND end_date >= %s
        """,
        [data.employee_id, data.end_date, data.start_date],
    ).fetchone()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scheduling Conflict: Employee {data.employee_id} is already allocated to {conflict['project_id']} ({conflict['employee_allocation_id']}) in this period.",
        )

    new_id = generate_next_id(db, "employee_allocations", "employee_allocation_id", "EMPA-")
    db.execute(
        """
        INSERT INTO employee_allocations (employee_allocation_id, project_id, employee_id, start_date, end_date, role, allocation_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.project_id, data.employee_id, data.start_date, data.end_date, data.role, data.allocation_status],
    )
    return {**data.model_dump(), "employee_allocation_id": new_id}


@router.patch("/employee-allocations/{employee_allocation_id}", summary="Update employee allocation")
def update_employee_allocation(employee_allocation_id: str, data: PartialEmployeeAllocationInput, db: Database) -> dict[str, Any]:
    """Reschedule or change worker on an allocation with date overlap checking."""
    existing = db.execute("SELECT * FROM employee_allocations WHERE employee_allocation_id = %s", [employee_allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {employee_allocation_id} not found")

    new_emp_id = data.employee_id if data.employee_id is not None else existing["employee_id"]
    new_start = data.start_date if data.start_date is not None else existing["start_date"]
    new_end = data.end_date if data.end_date is not None else existing["end_date"]
    new_status = data.allocation_status if data.allocation_status is not None else existing["allocation_status"]
    new_role = data.role if data.role is not None else existing["role"]
    new_project = data.project_id if data.project_id is not None else existing["project_id"]

    if new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    if new_status not in ("Completed", "Cancelled"):
        conflict = db.execute(
            """
            SELECT employee_allocation_id, project_id FROM employee_allocations
            WHERE employee_id = %s
              AND employee_allocation_id != %s
              AND allocation_status NOT IN ('Completed', 'Cancelled')
              AND start_date <= %s
              AND end_date >= %s
            """,
            [new_emp_id, employee_allocation_id, new_end, new_start],
        ).fetchone()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Employee {new_emp_id} is already allocated to {conflict['project_id']} ({conflict['employee_allocation_id']}).",
            )

    db.execute(
        """
        UPDATE employee_allocations
        SET project_id = %s, employee_id = %s, start_date = %s, end_date = %s, role = %s, allocation_status = %s
        WHERE employee_allocation_id = %s
        """,
        [new_project, new_emp_id, new_start, new_end, new_role, new_status, employee_allocation_id],
    )
    updated = db.execute("SELECT * FROM employee_allocations WHERE employee_allocation_id = %s", [employee_allocation_id]).fetchone()
    return serialize_row(updated)


@router.patch("/employee-allocations/{employee_allocation_id}/status", summary="Update employee allocation status")
def update_employee_allocation_status(employee_allocation_id: str, body: AllocationStatusUpdate, db: Database) -> dict[str, Any]:
    """Change employee allocation status. Validates allocation exists first."""
    existing = db.execute("SELECT * FROM employee_allocations WHERE employee_allocation_id = %s", [employee_allocation_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {employee_allocation_id} not found")

    db.execute(
        "UPDATE employee_allocations SET allocation_status = %s WHERE employee_allocation_id = %s",
        [body.allocation_status, employee_allocation_id],
    )
    return {"employee_allocation_id": employee_allocation_id, "allocation_status": body.allocation_status}


@router.delete("/employee-allocations/{employee_allocation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete employee allocation")
def delete_employee_allocation(employee_allocation_id: str, db: Database) -> None:
    """Delete an employee allocation record."""
    res = db.execute("DELETE FROM employee_allocations WHERE employee_allocation_id = %s", [employee_allocation_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {employee_allocation_id} not found")
