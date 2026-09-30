"""
BuildSync Database Management & Connection Dependency
======================================================
This module establishes connection management using psycopg v3,
handles database auto-initialization from the database/ schema and seed CSVs,
provides secure SQL ID generation with table whitelisting, and provides
standardized row serialization for JSON compatibility.
"""

from datetime import date, datetime
from decimal import Decimal
import importlib.util
import os
from pathlib import Path
from typing import Annotated, Any, Iterator

from dotenv import load_dotenv
from fastapi import Depends
from psycopg import Connection, connect
from psycopg.rows import dict_row

# --------------------------------------------------------------------------
# Environment Loading: check backend/.env, root .env, then system environment
# --------------------------------------------------------------------------
backend_env = Path(__file__).resolve().parent.parent / ".env"
root_env = Path(__file__).resolve().parent.parent.parent / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
if root_env.exists():
    load_dotenv(root_env)
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

# Whitelist of tables and their primary key columns for secure ID generation
ALLOWED_TABLE_COLUMNS: dict[str, str] = {
    "projects": "project_id",
    "project_schedules": "schedule_id",
    "equipment": "equipment_id",
    "vehicles": "vehicle_id",
    "maintenance_records": "maintenance_id",
    "equipment_allocations": "allocation_id",
    "vehicle_allocations": "vehicle_allocation_id",
    "employees": "employee_id",
    "contractors": "contractor_id",
    "employee_allocations": "employee_allocation_id",
    "materials": "material_id",
    "suppliers": "supplier_id",
    "material_allocations": "material_allocation_id",
    "budgets": "budget_id",
}


def get_connection() -> Iterator[Connection[dict[str, Any]]]:
    """
    FastAPI dependency yielding a psycopg v3 connection with dictionary row access.
    Autocommit is enabled to ensure data modifications persist immediately.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set in .env to a valid PostgreSQL connection string.")
    with connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as connection:
        yield connection


Database = Annotated[Connection[dict[str, Any]], Depends(get_connection)]


def initialize_database() -> None:
    """
    Startup hook: Checks if the BuildSync schema exists in PostgreSQL.
    If missing, loads and executes 'database/buildsync_schema.sql'.
    If the tables are empty, executes 'database/import_data.py' to seed 7,000 records.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set to start the API.")

    with connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as connection:
        # Check if the primary projects table exists
        row = connection.execute("SELECT to_regclass('public.projects') AS tbl").fetchone()
        schema_path = Path(__file__).resolve().parent.parent.parent / "database" / "buildsync_schema.sql"

        if not row or not row.get("tbl"):
            if schema_path.exists():
                schema_sql = schema_path.read_text(encoding="utf-8")
                connection.execute(schema_sql)

        # Check if seed data exists; if empty, automatically import from the groupmate's dataset
        count_row = connection.execute("SELECT count(*) AS cnt FROM projects").fetchone()
        if count_row and count_row.get("cnt", 0) == 0:
            import_script = Path(__file__).resolve().parent.parent.parent / "database" / "import_data.py"
            if import_script.exists():
                spec = importlib.util.spec_from_file_location("buildsync_import_data", str(import_script))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "main"):
                        mod.main()

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS material_consumption_history (
                consumption_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                project_id VARCHAR(20) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
                material_id VARCHAR(20) NOT NULL REFERENCES materials(material_id) ON DELETE CASCADE,
                quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
                consumed_on DATE NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS project_cost_history (
                cost_entry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                project_id VARCHAR(20) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
                amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
                incurred_on DATE NOT NULL,
                description VARCHAR(250)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_material_consumption_material_date "
            "ON material_consumption_history(material_id, consumed_on)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_project_cost_history_project_date "
            "ON project_cost_history(project_id, incurred_on)"
        )

        # Keep existing databases compatible with task-level resource assignments.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_resource_assignments (
                assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                schedule_id VARCHAR(20) NOT NULL REFERENCES project_schedules(schedule_id) ON DELETE CASCADE,
                resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('employee', 'equipment', 'vehicle', 'material')),
                resource_id VARCHAR(20) NOT NULL,
                quantity NUMERIC(12,2) CHECK (quantity IS NULL OR quantity > 0),
                UNIQUE (schedule_id, resource_type, resource_id)
            )
            """
        )


def generate_next_id(db: Connection[dict[str, Any]], table: str, id_column: str, prefix: str) -> str:
    """
    Generate the next sequential ID in the format '{PREFIX}{0001}' (e.g. PRJ-0001, EQ-0001).
    Applies strict table & column whitelisting to guarantee SQL injection safety.
    Uses LENGTH ordering so numeric keys sort correctly beyond 4 digits.
    """
    if table not in ALLOWED_TABLE_COLUMNS or ALLOWED_TABLE_COLUMNS[table] != id_column:
        raise ValueError(f"Security error: Invalid table '{table}' or id_column '{id_column}' for ID generation.")

    # Safe to format because table and id_column are verified against ALLOWED_TABLE_COLUMNS
    query = f"SELECT {id_column} FROM {table} WHERE {id_column} LIKE %s ORDER BY LENGTH({id_column}) DESC, {id_column} DESC LIMIT 1"
    row = db.execute(query, [f"{prefix}%"]).fetchone()

    if not row or not row.get(id_column):
        return f"{prefix}0001"

    raw_id = str(row[id_column])
    try:
        num_part = int(raw_id.split("-")[-1])
        return f"{prefix}{num_part + 1:04d}"
    except (IndexError, ValueError):
        return f"{prefix}0001"


def serialize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Converts PostgreSQL specific data types (date, datetime, Decimal) into standard JSON-serializable types.
    """
    if row is None:
        return None
    res = {}
    for k, v in row.items():
        if isinstance(v, (date, datetime)):
            res[k] = v.isoformat()
        elif isinstance(v, Decimal):
            res[k] = float(v)
        elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
            res[k] = float(v)
        else:
            res[k] = v
    return res
