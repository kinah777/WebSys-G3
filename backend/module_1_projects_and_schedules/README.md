# Module 1: Projects & Schedules

This module manages construction projects, milestone schedules, dependencies, and dynamic progress calculation.

## Database Tables
- `projects` (ID prefix: `PRJ-`, e.g., `PRJ-0001`)
- `project_schedules` (ID prefix: `SCH-`, e.g., `SCH-0001`)

## Endpoints

### Projects
- `GET /projects` - List all projects (supports query `?status=Planning` and `?limit=100`)
- `GET /projects/{project_id}` - Retrieve details of a single project
- `POST /projects` - Create a new project (auto-generates `PRJ-xxxx` ID)
- `PATCH /projects/{project_id}` - Partial update of project attributes
- `DELETE /projects/{project_id}` - Delete project

### Schedules
- `GET /schedules` (or `/project-schedules`) - List schedule tasks (supports `?project_id=PRJ-0001`)
- `GET /schedules/{schedule_id}` - Get schedule task by ID
- `POST /schedules` - Create milestone task (auto-generates `SCH-xxxx` ID, checks parent project exists)
- `PATCH /schedules/{schedule_id}` - Partial update of schedule task
- `DELETE /schedules/{schedule_id}` - Delete schedule task

### Complex Endpoints
- `GET /projects/{project_id}/progress` - Dynamically recalculates completion percentage from completed milestone tasks and syncs it back to the database.
- `GET /projects/{project_id}/timeline` - Returns chronological milestones and task dependencies for Gantt charts.
