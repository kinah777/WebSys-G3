"""
Module 4: Materials & Supply Chain (Procurement) Router
======================================================
Manages site materials inventory, suppliers, material requisitioning allocations,
low-stock procurement alerts, and budget procurement feasibility checks.

Endpoints:
- Materials: GET /materials, GET /materials/{id}, POST, PATCH, DELETE
- Suppliers: GET /suppliers, GET /suppliers/{id}, POST, PATCH, DELETE
- Allocations: GET, POST (with stock check & deduction), PATCH status, DELETE (restores stock)
- Complex: POST /materials/{id}/restock, GET /materials/alerts/low-stock, GET /procurement/budget-check/{project_id}
"""

from datetime import date
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.database import Database, generate_next_id, serialize_row
from app.forecasting import forecast_monthly_series
from .models import (
    Material,
    MaterialAllocation,
    MaterialAllocationInput,
    MaterialAllocationStatusUpdate,
    MaterialConsumptionInput,
    MaterialInput,
    PartialMaterialInput,
    PartialSupplierInput,
    RestockInput,
    Supplier,
    SupplierInput,
)

router = APIRouter(tags=["Module 4: Materials & Supply Chain (Procurement)"])


@router.post("/materials/consumption", status_code=status.HTTP_201_CREATED, summary="Record actual material consumption")
def record_material_consumption(data: MaterialConsumptionInput, db: Database) -> dict[str, Any]:
    if data.consumed_on > date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consumption date cannot be in the future")
    row = db.execute(
        """
        INSERT INTO material_consumption_history (project_id, material_id, quantity, consumed_on)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        [data.project_id, data.material_id, data.quantity, data.consumed_on],
    ).fetchone()
    return serialize_row(row)


@router.get("/materials/{material_id}/forecast/demand", summary="Forecast monthly material demand with ARIMA")
def material_demand_forecast(
    material_id: str,
    db: Database,
    periods: int = Query(3, ge=1, le=24),
) -> dict[str, Any]:
    material = db.execute(
        "SELECT material_id, name, unit, unit_cost FROM materials WHERE material_id = %s",
        [material_id],
    ).fetchone()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")

    rows = db.execute(
        """
        SELECT TO_CHAR(DATE_TRUNC('month', consumed_on), 'YYYY-MM') AS month,
               SUM(quantity) AS value
        FROM material_consumption_history
        WHERE material_id = %s AND consumed_on <= CURRENT_DATE
        GROUP BY DATE_TRUNC('month', consumed_on)
        ORDER BY DATE_TRUNC('month', consumed_on)
        """,
        [material_id],
    ).fetchall()
    result = forecast_monthly_series(
        [(row["month"], float(row["value"])) for row in rows], periods
    )
    unit_cost = float(material["unit_cost"] or 0)
    return {
        "material_id": material_id,
        "material_name": material["name"],
        "unit": material["unit"],
        "unit_cost": unit_cost,
        "status": result["status"],
        "observations": result["observations"],
        "forecast": [
            {
                "month": point["month"],
                "demand_quantity": point["value"],
                "projected_material_cost": round(float(point["value"]) * unit_cost, 2),
            }
            for point in result["forecast"]
        ],
        "minimum_observations": result["minimum_observations"],
    }


# ==========================================================================
# 1. Materials & Inventory Management
# ==========================================================================
@router.get("/materials", response_model=list[Material], summary="List all materials in inventory")
def list_materials(
    db: Database,
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List site construction materials and current stock levels."""
    rows = db.execute("SELECT * FROM materials ORDER BY material_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


# ── IMPORTANT: Static route BEFORE parameterized /{material_id} to prevent path masking ──
@router.get("/materials/alerts/low-stock", summary="List low-stock materials needing reorder")
def get_low_stock_materials(db: Database) -> list[dict[str, Any]]:
    """
    Complex Functionality:
    Procurement requisition engine: identifies all materials whose current quantity is at or below
    the reorder threshold, calculating the shortage volume and estimated restock budget.
    """
    rows = db.execute(
        """
        SELECT
            material_id,
            name,
            type,
            unit,
            quantity_in_stock,
            reorder_level,
            unit_cost,
            (reorder_level - quantity_in_stock) AS shortage_quantity,
            ROUND(((reorder_level - quantity_in_stock) * unit_cost)::numeric, 2) AS estimated_procurement_cost
        FROM materials
        WHERE quantity_in_stock <= reorder_level
        ORDER BY (quantity_in_stock / NULLIF(reorder_level, 0)) ASC NULLS FIRST
        """
    ).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/materials/{material_id}", response_model=Material, summary="Get material details by ID")
def get_material(material_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single material item."""
    row = db.execute("SELECT * FROM materials WHERE material_id = %s", [material_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")
    return serialize_row(row)


@router.post("/materials", response_model=Material, status_code=status.HTTP_201_CREATED, summary="Create a new material item")
def create_material(data: MaterialInput, db: Database) -> dict[str, Any]:
    """Add a new material item to inventory catalog with server-assigned ID (MAT-xxxx)."""
    new_id = generate_next_id(db, "materials", "material_id", "MAT-")
    db.execute(
        """
        INSERT INTO materials (material_id, name, type, unit, quantity_in_stock, reorder_level, unit_cost)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.name, data.type, data.unit, data.quantity_in_stock, data.reorder_level, data.unit_cost],
    )
    return {**data.model_dump(), "material_id": new_id}


@router.patch("/materials/{material_id}", response_model=Material, summary="Partially update material details")
def update_material(material_id: str, data: PartialMaterialInput, db: Database) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM materials WHERE material_id = %s", [material_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")

    merged = {
        "name": data.name if data.name is not None else existing["name"],
        "type": data.type if data.type is not None else existing["type"],
        "unit": data.unit if data.unit is not None else existing["unit"],
        "quantity_in_stock": data.quantity_in_stock if data.quantity_in_stock is not None else existing["quantity_in_stock"],
        "reorder_level": data.reorder_level if data.reorder_level is not None else existing["reorder_level"],
        "unit_cost": data.unit_cost if data.unit_cost is not None else existing["unit_cost"],
    }
    db.execute(
        """
        UPDATE materials
        SET name = %s, type = %s, unit = %s, quantity_in_stock = %s, reorder_level = %s, unit_cost = %s
        WHERE material_id = %s
        """,
        [merged["name"], merged["type"], merged["unit"], merged["quantity_in_stock"], merged["reorder_level"], merged["unit_cost"], material_id],
    )
    return {**merged, "material_id": material_id}


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete material")
def delete_material(material_id: str, db: Database) -> None:
    """Delete a material item from catalog."""
    res = db.execute("DELETE FROM materials WHERE material_id = %s", [material_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")


@router.post("/materials/{material_id}/restock", response_model=Material, summary="Restock material inventory")
def restock_material(material_id: str, data: RestockInput, db: Database) -> dict[str, Any]:
    """Restock an existing material item with incoming shipment quantity."""
    existing = db.execute("SELECT * FROM materials WHERE material_id = %s", [material_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")

    new_stock = float(existing["quantity_in_stock"]) + data.quantity
    new_cost = data.unit_cost if data.unit_cost is not None else float(existing["unit_cost"])

    db.execute(
        "UPDATE materials SET quantity_in_stock = %s, unit_cost = %s WHERE material_id = %s",
        [new_stock, new_cost, material_id],
    )
    updated = db.execute("SELECT * FROM materials WHERE material_id = %s", [material_id]).fetchone()
    return serialize_row(updated)


# ==========================================================================
# 2. Suppliers Management
# ==========================================================================
@router.get("/suppliers", response_model=list[Supplier], summary="List all suppliers")
def list_suppliers(
    db: Database,
    filter_status: str | None = Query(None, alias="status", description="Active, Inactive"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List verified external vendors and material suppliers."""
    if filter_status:
        rows = db.execute(
            "SELECT * FROM suppliers WHERE status = %s ORDER BY supplier_id LIMIT %s",
            [filter_status, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM suppliers ORDER BY supplier_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/suppliers/{supplier_id}", response_model=Supplier, summary="Get supplier details by ID")
def get_supplier(supplier_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single supplier."""
    row = db.execute("SELECT * FROM suppliers WHERE supplier_id = %s", [supplier_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier {supplier_id} not found")
    return serialize_row(row)


@router.post("/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED, summary="Create a supplier")
def create_supplier(data: SupplierInput, db: Database) -> dict[str, Any]:
    """Register a new material supplier with server-assigned ID (SUP-xxxx)."""
    new_id = generate_next_id(db, "suppliers", "supplier_id", "SUP-")
    db.execute(
        """
        INSERT INTO suppliers (supplier_id, name, contact_person, phone, location, supplier_rating, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.name, data.contact_person, data.phone, data.location, data.supplier_rating, data.status],
    )
    return {**data.model_dump(), "supplier_id": new_id}


@router.patch("/suppliers/{supplier_id}", response_model=Supplier, summary="Partially update supplier details")
def update_supplier(supplier_id: str, data: PartialSupplierInput, db: Database) -> dict[str, Any]:
    """Partial update: only the fields included in the request body will be changed."""
    existing = db.execute("SELECT * FROM suppliers WHERE supplier_id = %s", [supplier_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier {supplier_id} not found")

    merged = {
        "name": data.name if data.name is not None else existing["name"],
        "contact_person": data.contact_person if data.contact_person is not None else existing["contact_person"],
        "phone": data.phone if data.phone is not None else existing["phone"],
        "location": data.location if data.location is not None else existing["location"],
        "supplier_rating": data.supplier_rating if data.supplier_rating is not None else existing["supplier_rating"],
        "status": data.status if data.status is not None else existing["status"],
    }
    db.execute(
        """
        UPDATE suppliers
        SET name = %s, contact_person = %s, phone = %s, location = %s, supplier_rating = %s, status = %s
        WHERE supplier_id = %s
        """,
        [merged["name"], merged["contact_person"], merged["phone"], merged["location"], merged["supplier_rating"], merged["status"], supplier_id],
    )
    return {**merged, "supplier_id": supplier_id}


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete supplier")
def delete_supplier(supplier_id: str, db: Database) -> None:
    """Delete a supplier record."""
    res = db.execute("DELETE FROM suppliers WHERE supplier_id = %s", [supplier_id])
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier {supplier_id} not found")


# ==========================================================================
# 3. Material Allocations (with stock validation & auto-deduction)
# ==========================================================================
@router.get("/material-allocations", response_model=list[MaterialAllocation], summary="List material allocations")
def list_material_allocations(
    db: Database,
    project_id: str | None = Query(None, description="Filter by project ID"),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List project material allocations and usage records."""
    if project_id:
        rows = db.execute(
            "SELECT * FROM material_allocations WHERE project_id = %s ORDER BY material_allocation_id LIMIT %s",
            [project_id, limit],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM material_allocations ORDER BY material_allocation_id LIMIT %s", [limit]).fetchall()
    return [serialize_row(r) for r in rows]


@router.get("/material-allocations/{material_allocation_id}", response_model=MaterialAllocation, summary="Get material allocation by ID")
def get_material_allocation(material_allocation_id: str, db: Database) -> dict[str, Any]:
    """Retrieve details for a single material allocation."""
    row = db.execute("SELECT * FROM material_allocations WHERE material_allocation_id = %s", [material_allocation_id]).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {material_allocation_id} not found")
    return serialize_row(row)


@router.post("/material-allocations", response_model=MaterialAllocation, status_code=status.HTTP_201_CREATED, summary="Allocate materials with stock validation")
def create_material_allocation(data: MaterialAllocationInput, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Allocates materials to a project and automatically deducts allocated quantity from available inventory.
    Returns HTTP 409 Conflict if requested quantity exceeds current stock.
    """
    if not db.execute("SELECT 1 FROM projects WHERE project_id = %s", [data.project_id]).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found")

    material = db.execute(
        "SELECT quantity_in_stock, name FROM materials WHERE material_id = %s",
        [data.material_id],
    ).fetchone()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {data.material_id} not found")

    in_stock = float(material["quantity_in_stock"])
    if in_stock < data.quantity_required:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock for {material['name']} ({data.material_id}). In stock: {in_stock}, requested: {data.quantity_required}",
        )

    new_id = generate_next_id(db, "material_allocations", "material_allocation_id", "MA-")
    db.execute(
        """
        INSERT INTO material_allocations (material_allocation_id, project_id, material_id, quantity_required, quantity_used, required_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [new_id, data.project_id, data.material_id, data.quantity_required, data.quantity_used, data.required_date, data.status],
    )
    # Deduct material stock
    db.execute(
        "UPDATE materials SET quantity_in_stock = quantity_in_stock - %s WHERE material_id = %s",
        [data.quantity_required, data.material_id],
    )
    return {**data.model_dump(), "material_allocation_id": new_id}


@router.patch("/material-allocations/{material_allocation_id}/status", summary="Update material allocation status")
def update_material_allocation_status(material_allocation_id: str, body: MaterialAllocationStatusUpdate, db: Database) -> dict[str, Any]:
    """
    Update material allocation status. Validates allocation exists first.
    If cancelled, returns the allocated quantity back to material inventory.
    """
    existing = db.execute(
        "SELECT * FROM material_allocations WHERE material_allocation_id = %s",
        [material_allocation_id],
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {material_allocation_id} not found")

    old_status = existing.get("status", "")
    new_status = body.status

    db.execute(
        "UPDATE material_allocations SET status = %s WHERE material_allocation_id = %s",
        [new_status, material_allocation_id],
    )

    # Return stock to inventory when cancelling an allocation that was not already cancelled
    if new_status == "Cancelled" and old_status != "Cancelled":
        qty = float(existing.get("quantity_required", 0))
        if qty > 0:
            db.execute(
                "UPDATE materials SET quantity_in_stock = quantity_in_stock + %s WHERE material_id = %s",
                [qty, existing["material_id"]],
            )

    return {"material_allocation_id": material_allocation_id, "status": new_status}


@router.delete("/material-allocations/{material_allocation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete material allocation")
def delete_material_allocation(material_allocation_id: str, db: Database) -> None:
    """
    Delete a material allocation record.
    Returns the allocated quantity back to material inventory (unless already cancelled).
    """
    existing = db.execute(
        "SELECT material_id, quantity_required, status FROM material_allocations WHERE material_allocation_id = %s",
        [material_allocation_id],
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation {material_allocation_id} not found")

    if existing.get("status") != "Cancelled":
        qty = float(existing.get("quantity_required", 0))
        if qty > 0:
            db.execute(
                "UPDATE materials SET quantity_in_stock = quantity_in_stock + %s WHERE material_id = %s",
                [qty, existing["material_id"]],
            )

    db.execute("DELETE FROM material_allocations WHERE material_allocation_id = %s", [material_allocation_id])


# ==========================================================================
# 4. Procurement Budget Feasibility Check
# ==========================================================================
@router.get("/procurement/budget-check/{project_id}", summary="Check if project budget can cover pending material orders")
def check_procurement_budget(project_id: str, db: Database) -> dict[str, Any]:
    """
    Complex Functionality:
    Cross-checks pending scheduled materials in Module 4 against the remaining project budget in Module 5.
    Returns whether there is a budget shortfall and the exact deficit amount.
    """
    budget = db.execute("SELECT remaining_budget, allocated_budget FROM budgets WHERE project_id = %s", [project_id]).fetchone()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No budget found for project {project_id}")

    pending = db.execute(
        """
        SELECT COALESCE(SUM(ma.quantity_required * m.unit_cost), 0) AS pending_material_cost
        FROM material_allocations ma
        JOIN materials m ON m.material_id = ma.material_id
        WHERE ma.project_id = %s AND ma.status = 'Scheduled'
        """,
        [project_id],
    ).fetchone()

    pending_cost = float(pending["pending_material_cost"] or 0.0)
    remaining = float(budget["remaining_budget"] or 0.0)
    has_shortfall = pending_cost > remaining

    return {
        "project_id": project_id,
        "remaining_budget": remaining,
        "pending_material_procurement_cost": round(pending_cost, 2),
        "has_budget_shortfall": has_shortfall,
        "shortfall_amount": round(pending_cost - remaining, 2) if has_shortfall else 0.0,
    }
