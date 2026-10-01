"""
Module 1: Projects & Schedules Router
=====================================
Handles project lifecycles, milestone schedules, task dependencies,
and dynamic project progress calculation.

Endpoints:
- Projects: GET /projects, GET /projects/{id}, POST /projects, PATCH /projects/{id}, DELETE /projects/{id}
- Schedules: GET /schedules (and /project-schedules), GET /{id}, POST, PATCH /{id}, DELETE /{id}
- Complex: GET /projects/{id}/progress, GET /projects/{id}/timeline
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_roles
from app.database import Database, generate_next_id, serialize_row
from .models import (
    PartialProjectInput,
    PartialScheduleInput,
    Project,
    ProjectInput,
    Schedule,
    ScheduleInput,
    TaskResourceAssignment,
    TaskResourceAssignmentInput,
)

router = APIRouter(tags=["Module 1: Projects & Schedules"])


# ==========================================================================
# 1. Construction Projects Management
# ==========================================================================
@router.get("/projects", response_model=list[Project], summary="List all projects with optional status filter")
def list_projects(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Filter by status (Planning, Ongoing, Completed, On Hold)"),
    limit: int = Query(600, ge=1, le=600, description="Max number of records to return"),
) -> list[dict[str, Any]]:
    """List construction projects with optional status filtering and pagination limit."""
    if filter_status:
        rows = db.execute(
            "SELECT * FROM projects WHERE status = %s ORDER BY project_id LIMIT %s",
            [filter_status, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM projects ORDER BY project_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/projects/{project_id}", response_model=Project, summary="Get project by ID")
def get_project(project_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single project by its primary key ID (e.g. PRJ-0001)."""
    row = db.execute("SELECT * FROM projects WHERE project_id = %s", [project_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")
    return serialize_row(row)


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED, summary="Create a new project")
def create_project(data: ProjectInput, db: Database) -> dict[str, Any]:
    """Create a new project with server-generated ID (PRJ-xxxx) and date validation."""
    if data.start_date and data.end_date and data.start_date > data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    new_id = generate_next_id(db, "projects", "project_id", "PRJ-")
    db.execute(
        """
        INSERT INTO projects (project_id, project_name, project_type, location, start_date, end_date, budget, priority, status, completion_percentage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            new_id, data.project_name, data.project_type, data.location,
            data.start_date, data.end_date, data.budget, data.priority,
            data.status, data.completion_percentage,
        ],
    )
    return {**data.model_dump(), "project_id": new_id}


@router.patch("/projects/{project_id}", response_model=Project, summary="Partially update an existing project")
def update_project(project_id: str, data: PartialProjectInput, db: Database) -> dict[str, Any]:
    """
    Partial update: only the fields included in the request body will be changed.
    Unspecified fields retain their current database values.
    """
    existing = db.execute("SELECT * FROM projects WHERE project_id = %s", [project_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    merged = {
        "project_name": data.project_name if data.project_name is not None else existing["project_name"],
        "project_type": data.project_type if data.project_type is not None else existing["project_type"],
        "location": data.location if data.location is not None else existing["location"],
        "start_date": data.start_date if data.start_date is not None else existing["start_date"],
        "end_date": data.end_date if data.end_date is not None else existing["end_date"],
        "budget": data.budget if data.budget is not None else existing["budget"],
        "priority": data.priority if data.priority is not None else existing["priority"],
        "status": data.status if data.status is not None else existing["status"],
        "completion_percentage": data.completion_percentage if data.completion_percentage is not None else existing["completion_percentage"],
    }

    if merged["start_date"] and merged["end_date"] and merged["start_date"] > merged["end_date"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    db.execute(
        """
        UPDATE projects
        SET project_name = %s, project_type = %s, location = %s, start_date = %s, end_date = %s,
            budget = %s, priority = %s, status = %s, completion_percentage = %s
        WHERE project_id = %s
        """,
        [
            merged["project_name"], merged["project_type"], merged["location"], merged["start_date"],
            merged["end_date"], merged["budget"], merged["priority"], merged["status"],
            merged["completion_percentage"], project_id,
        ],
    )
    return {**merged, "project_id": project_id}


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a project")
def delete_project(project_id: str, db: Database) -> None:
    """Delete a project and its associated cascading records."""
    res = db.execute("DELETE FROM projects WHERE project_id = %s", [project_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")


# ==========================================================================
# 2. Project Schedules & Milestones
# (Supports both /schedules and /project-schedules paths)
# ==========================================================================
@router.get("/project-schedules", response_model=list[Schedule], summary="List project schedule tasks")
@router.get("/schedules", response_model=list[Schedule], summary="List schedule tasks (alias)")
def list_schedules(
    db: Database,
    project_id: str | None = Query(None, description="Filter by project ID"),
    limit: int = Query(600, ge=1, le=600),
) -> list[dict[str, Any]]:
    """List project schedule tasks with optional project_id filter."""
    if project_id:
        rows = db.execute(
            "SELECT * FROM project_schedules WHERE project_id = %s ORDER BY schedule_id LIMIT %s",
            [project_id, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM project_schedules ORDER BY schedule_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/project-schedules/{schedule_id}", response_model=Schedule, summary="Get schedule task by ID")
@router.get("/schedules/{schedule_id}", response_model=Schedule, summary="Get schedule task by ID (alias)")
def get_schedule(schedule_id: str, db: Database) -> dict[str, Any]:
    """Retrieve a single schedule task by schedule_id (e.g. SCH-0001)."""
    row = db.execute("SELECT * FROM project_schedules WHERE schedule_id = %s", [schedule_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")
    return serialize_row(row)


@router.post("/project-schedules", response_model=Schedule, status_code=status.HTTP_201_CREATED, summary="Create a schedule task")
@router.post("/schedules", response_model=Schedule, status_code=status.HTTP_201_CREATED, summary="Create a schedule task (alias)")
def create_schedule(
    data: ScheduleInput,
    db: Database,
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    """Create a new schedule milestone task with validation that the project exists."""
    if data.start_date and data.end_date and data.start_date > data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    project_check = db.execute("SELECT project_id FROM projects WHERE project_id = %s", [data.project_id]).fetchone()
    if not project_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parent project {data.project_id} does not exist.")

    new_id = generate_next_id(db, "project_schedules", "schedule_id", "SCH-")
    db.execute(
        """
        INSERT INTO project_schedules (schedule_id, project_id, task_name, start_date, end_date, duration_days, dependency, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            new_id, data.project_id, data.task_name, data.start_date,
            data.end_date, data.duration_days, data.dependency, data.status,
        ],
    )
    return {**data.model_dump(), "schedule_id": new_id}


@router.patch("/project-schedules/{schedule_id}", response_model=Schedule, summary="Partially update a schedule task")
@router.patch("/schedules/{schedule_id}", response_model=Schedule, summary="Partially update a schedule task (alias)")
def update_schedule(
    schedule_id: str,
    data: PartialScheduleInput,
    db: Database,
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM project_schedules WHERE schedule_id = %s", [schedule_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")

    new_project_id = data.project_id if data.project_id is not None else existing["project_id"]
    if data.project_id is not None and data.project_id != existing["project_id"]:
        proj_check = db.execute("SELECT project_id FROM projects WHERE project_id = %s", [new_project_id]).fetchone()
        if not proj_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parent project {new_project_id} does not exist.")

    merged = {
        "project_id": new_project_id,
        "task_name": data.task_name if data.task_name is not None else existing["task_name"],
        "start_date": data.start_date if data.start_date is not None else existing["start_date"],
        "end_date": data.end_date if data.end_date is not None else existing["end_date"],
        "duration_days": data.duration_days if data.duration_days is not None else existing["duration_days"],
        "dependency": data.dependency if data.dependency is not None else existing["dependency"],
        "status": data.status if data.status is not None else existing["status"],
    }

    if merged["start_date"] and merged["end_date"] and merged["start_date"] > merged["end_date"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")

    db.execute(
        """
        UPDATE project_schedules
        SET project_id = %s, task_name = %s, start_date = %s, end_date = %s,
            duration_days = %s, dependency = %s, status = %s
        WHERE schedule_id = %s
        """,
        [
            merged["project_id"], merged["task_name"], merged["start_date"], merged["end_date"],
            merged["duration_days"], merged["dependency"], merged["status"], schedule_id,
        ],
    )
    return {**merged, "schedule_id": schedule_id}


@router.delete("/project-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a schedule task")
@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a schedule task (alias)")
def delete_schedule(
    schedule_id: str,
    db: Database,
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> None:
    """Delete a schedule milestone task."""
    res = db.execute("DELETE FROM project_schedules WHERE schedule_id = %s", [schedule_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")


_TASK_RESOURCE_CONFIG = {
    "employee": {
        "table": "employees", "id": "employee_id", "label": "name",
        "allocations": "employee_allocations", "allocation_id": "employee_id",
    },
    "equipment": {
        "table": "equipment", "id": "equipment_id", "label": "name",
        "allocations": "equipment_allocations", "allocation_id": "equipment_id",
    },
    "vehicle": {
        "table": "vehicles", "id": "vehicle_id", "label": "plate_number",
        "allocations": "vehicle_allocations", "allocation_id": "vehicle_id",
    },
    "material": {
        "table": "materials", "id": "material_id", "label": "name",
    },
}


@router.get(
    "/project-schedules/{schedule_id}/assignments",
    response_model=list[TaskResourceAssignment],
    summary="List resources assigned directly to a task",
)
def list_task_assignments(schedule_id: str, db: Database) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM project_schedules WHERE schedule_id = %s", [schedule_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")

    rows = db.execute(
        """
        SELECT
            a.assignment_id,
            a.schedule_id,
            a.resource_type,
            a.resource_id,
            a.quantity,
            CASE a.resource_type
                WHEN 'employee' THEN (SELECT name FROM employees WHERE employee_id = a.resource_id)
                WHEN 'equipment' THEN (SELECT name FROM equipment WHERE equipment_id = a.resource_id)
                WHEN 'vehicle' THEN (SELECT plate_number FROM vehicles WHERE vehicle_id = a.resource_id)
                WHEN 'material' THEN (SELECT name FROM materials WHERE material_id = a.resource_id)
            END AS resource_name
        FROM task_resource_assignments a
        WHERE a.schedule_id = %s
        ORDER BY a.assignment_id
        """,
        [schedule_id],
    ).fetchall()
    return [serialize_row(row) for row in rows]


@router.post(
    "/project-schedules/{schedule_id}/assignments",
    response_model=TaskResourceAssignment,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a resource directly to a task",
)
def create_task_assignment(
    schedule_id: str,
    data: TaskResourceAssignmentInput,
    db: Database,
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    task = db.execute(
        "SELECT schedule_id, project_id, start_date, end_date, status FROM project_schedules WHERE schedule_id = %s",
        [schedule_id],
    ).fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")

    config = _TASK_RESOURCE_CONFIG[data.resource_type]
    resource = db.execute(
        f"SELECT {config['label']} AS resource_name FROM {config['table']} WHERE {config['id']} = %s",
        [data.resource_id],
    ).fetchone()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{data.resource_type.title()} {data.resource_id} not found")

    if data.resource_type == "material" and data.quantity is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="quantity is required for material assignments")

    if data.resource_type != "material":
        if not task["start_date"] or not task["end_date"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Set task start and end dates before assigning people or equipment.")

        task_conflict = db.execute(
            """
            SELECT a.assignment_id
            FROM task_resource_assignments a
            JOIN project_schedules s ON s.schedule_id = a.schedule_id
            WHERE a.resource_type = %s
              AND a.resource_id = %s
              AND a.schedule_id != %s
              AND s.status != 'Completed'
              AND s.start_date <= %s
              AND s.end_date >= %s
            LIMIT 1
            """,
            [data.resource_type, data.resource_id, schedule_id, task["end_date"], task["start_date"]],
        ).fetchone()
        if task_conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Resource {data.resource_id} is already assigned to another overlapping task.")

        allocation_conflict = db.execute(
            f"""
            SELECT 1 FROM {config['allocations']}
            WHERE {config['allocation_id']} = %s
              AND project_id != %s
              AND allocation_status NOT IN ('Completed', 'Cancelled')
              AND start_date <= %s
              AND end_date >= %s
            LIMIT 1
            """,
            [data.resource_id, task["project_id"], task["end_date"], task["start_date"]],
        ).fetchone()
        if allocation_conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Resource {data.resource_id} is already booked by another project during this task.")

    try:
        with db.transaction():
            existing = db.execute(
                "SELECT assignment_id FROM task_resource_assignments WHERE schedule_id = %s AND resource_type = %s AND resource_id = %s",
                [schedule_id, data.resource_type, data.resource_id],
            ).fetchone()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This resource is already assigned to the task.")

            if data.resource_type == "material":
                stock_update = db.execute(
                    "UPDATE materials SET quantity_in_stock = quantity_in_stock - %s WHERE material_id = %s AND quantity_in_stock >= %s",
                    [data.quantity, data.resource_id, data.quantity],
                )
                if stock_update.rowcount == 0:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not enough material is in stock for this assignment.")

            row = db.execute(
                """
                INSERT INTO task_resource_assignments (schedule_id, resource_type, resource_id, quantity)
                VALUES (%s, %s, %s, %s)
                RETURNING assignment_id, schedule_id, resource_type, resource_id, quantity
                """,
                [schedule_id, data.resource_type, data.resource_id, data.quantity],
            ).fetchone()
    except HTTPException:
        raise

    return {**serialize_row(row), "resource_name": resource["resource_name"]}


@router.delete(
    "/project-schedules/{schedule_id}/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a resource assignment from a task",
)
def delete_task_assignment(
    schedule_id: str,
    assignment_id: int,
    db: Database,
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> None:
    with db.transaction():
        assignment = db.execute(
            "DELETE FROM task_resource_assignments WHERE schedule_id = %s AND assignment_id = %s RETURNING resource_type, resource_id, quantity",
            [schedule_id, assignment_id],
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task resource assignment not found")
        if assignment["resource_type"] == "material" and assignment["quantity"]:
            db.execute(
                "UPDATE materials SET quantity_in_stock = quantity_in_stock + %s WHERE material_id = %s",
                [assignment["quantity"], assignment["resource_id"]],
            )


# ==========================================================================
# 3. Complex Functionality: Dynamic Progress Tracking & Timeline Gantt
# ==========================================================================
@router.get("/projects/{project_id}/progress", summary="Calculate and sync dynamic project progress")
def get_project_progress(project_id: str, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Dynamically computes project completion percentage from the ratio of
    completed schedule tasks, and synchronizes the value back to the database.
    """
    project = db.execute("SELECT * FROM projects WHERE project_id = %s", [project_id]).fetchone()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    tasks = db.execute("SELECT * FROM project_schedules WHERE project_id = %s", [project_id]).fetchall()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if str(t.get("status", "")).lower() == "completed")

    calc_percentage = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else float(project.get("completion_percentage") or 0.0)

    # Sync back to projects table if tasks exist
    if total_tasks > 0:
        db.execute(
            "UPDATE projects SET completion_percentage = %s WHERE project_id = %s",
            [calc_percentage, project_id],
        )

    return {
        "project_id": project_id,
        "project_name": project["project_name"],
        "status": project["status"],
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": calc_percentage,
    }


@router.get("/projects/{project_id}/timeline", summary="Get ordered timeline with task dependencies")
def get_project_timeline(project_id: str, db: Database) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Returns chronological timeline milestones for a project with task dependencies
    for rendering Gantt or milestone charts on the frontend.
    """
    project = db.execute("SELECT project_id FROM projects WHERE project_id = %s", [project_id]).fetchone()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    rows = db.execute(
        """
        SELECT schedule_id, task_name, start_date, end_date, duration_days, dependency, status
        FROM project_schedules
        WHERE project_id = %s
        ORDER BY start_date ASC NULLS LAST, schedule_id ASC
        """,
        [project_id],
    ).fetchall()
    return [serialize_row(r) for r in rows]
