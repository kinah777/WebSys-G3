"""
BuildSync - Construction Resource Management System Backend API
================================================================
Main FastAPI application file mounting CORS middleware, database lifespan
initialization, database exception handlers, and the 6 domain module routers.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path so modules resolve cleanly everywhere
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg.errors

from app.database import initialize_database
from module_1_projects_and_schedules import router as module_1_router
from module_2_equipment_and_fleet import router as module_2_router
from module_3_workforce_and_labor import router as module_3_router
from module_4_materials_and_supply_chain import router as module_4_router
from module_5_financials_and_forecasting import router as module_5_router
from module_6_conflict_resolution_center import router as module_6_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Application lifespan manager: runs database schema and dataset initialization
    on server startup before accepting client requests.
    """
    initialize_database()
    yield


app = FastAPI(
    title="BuildSync API",
    description="Backend API for BuildSync Construction Resource Management System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --------------------------------------------------------------------------
# Security & CORS Middleware
# --------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Global Exception Handlers for Database Integrity & Security
# --------------------------------------------------------------------------
@app.exception_handler(psycopg.errors.ForeignKeyViolation)
async def foreign_key_exception_handler(_: Request, exc: psycopg.errors.ForeignKeyViolation):
    """Clean HTTP 400 error message when an invalid foreign key is referenced."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Foreign key constraint violated: referenced entity does not exist in the database.", "error_type": "ForeignKeyViolation"},
    )


@app.exception_handler(psycopg.errors.UniqueViolation)
async def unique_violation_exception_handler(_: Request, exc: psycopg.errors.UniqueViolation):
    """Clean HTTP 409 conflict message when attempting to insert a duplicate unique value."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Duplicate record error: a record with this unique identifier or attribute already exists.", "error_type": "UniqueViolation"},
    )


@app.exception_handler(psycopg.errors.IntegrityError)
async def integrity_error_exception_handler(_: Request, exc: psycopg.errors.IntegrityError):
    """Clean HTTP 400 error message for general database constraint violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity constraint error.", "error_type": "IntegrityError"},
    )


# --------------------------------------------------------------------------
# System Health & Root Route
# --------------------------------------------------------------------------
@app.get("/", tags=["System Root"])
def root() -> dict[str, str]:
    """Root endpoint for health checking."""
    return {
        "system": "BuildSync API",
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# --------------------------------------------------------------------------
# Mount the 6 Core Module Routers
# --------------------------------------------------------------------------
app.include_router(module_1_router)   # Module 1 (Projects & Schedules)
app.include_router(module_2_router)   # Module 2 (Equipment & Fleet)
app.include_router(module_3_router)   # Module 3 (Workforce & Labor)
app.include_router(module_4_router)   # Module 4 (Materials & Supply Chain)
app.include_router(module_5_router)   # Module 5 (Financials & Forecasting)
app.include_router(module_6_router)   # Module 6 (Conflict Resolution Center)