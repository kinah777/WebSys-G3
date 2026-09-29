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
from fastapi import APIRouter, HTTPException, Query, status

from app.database import Database, generate_next_id, serialize_row
from .models import (
    PartialProjectInput,
    PartialScheduleInput,
    Project,
    ProjectInput,
    Schedule,
    ScheduleInput,
)

router = APIRouter(tags=["Module 1: Projects & Schedules"])


# ==========================================================================
# 1. Construction Projects Management
# ==========================================================================
@router.get("/projects", response_model=list[Project], summary="List all projects with optional status filter")
def list_projects(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Filter by status (Planning, Ongoing, Completed, On Hold)"),
    limit: int = Query(100, ge=1, le=500, description="Max number of records to return"),
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
    limit: int = Query(100, ge=1, le=500),
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
def create_schedule(data: ScheduleInput, db: Database) -> dict[str, Any]:
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
def update_schedule(schedule_id: str, data: PartialScheduleInput, db: Database) -> dict[str, Any]:
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
def delete_schedule(schedule_id: str, db: Database) -> None:
    """Delete a schedule milestone task."""
    res = db.execute("DELETE FROM project_schedules WHERE schedule_id = %s", [schedule_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule task {schedule_id} not found")


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
