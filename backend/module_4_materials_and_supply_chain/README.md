# Module 4: Materials & Supply Chain (Procurement)

This module manages site materials inventory, suppliers, material project allocations with stock check & auto-deduction, restock actions, and procurement feasibility checking.

## Database Tables
- `materials` (ID prefix: `MAT-`, e.g., `MAT-0001`)
- `suppliers` (ID prefix: `SUP-`, e.g., `SUP-0001`)
- `material_allocations` (ID prefix: `MA-`, e.g., `MA-0001`)

## Endpoints

### Materials Catalog
- `GET /materials` - List materials and stock levels
- `GET /materials/{material_id}` - Retrieve single material item
- `POST /materials` - Add new material item (auto-generates `MAT-xxxx`)
- `PATCH /materials/{material_id}` - Partial update of material details
- `DELETE /materials/{material_id}` - Delete material item

### Suppliers & Vendors
- `GET /suppliers` - List suppliers (supports `?status=Active` and `?limit=100`)
- `GET /suppliers/{supplier_id}` - Retrieve supplier details
- `POST /suppliers` - Register supplier (auto-generates `SUP-xxxx`)
- `PATCH /suppliers/{supplier_id}` - Partial update of supplier details
- `DELETE /suppliers/{supplier_id}` - Delete supplier record

### Material Allocations
- `GET /material-allocations` - List material allocations (supports `?project_id=PRJ-0001`)
- `GET /material-allocations/{material_allocation_id}` - Get single allocation
- `POST /material-allocations` - Allocate materials to project with stock verification (returns `409 Conflict` if insufficient stock, and automatically deducts from `quantity_in_stock`)
- `PATCH /material-allocations/{material_allocation_id}/status` - Update allocation status (if cancelled, restores deducted stock back to inventory)
- `DELETE /material-allocations/{material_allocation_id}` - Delete allocation (restores deducted stock back to inventory)

### Complex Endpoints
- `POST /materials/consumption` - Record actual consumption with a project, material, quantity, and consumption date for forecasting.
- `GET /materials/{material_id}/forecast/demand?periods=3` - Forecast monthly demand using ARIMA and return projected material cost at current unit cost. Requires at least six distinct months of recorded consumption.
- `POST /materials/{material_id}/restock` - Restocks inventory with incoming shipment and updates unit cost.
- `GET /materials/alerts/low-stock` - Returns all inventory items at or below reorder threshold with shortage quantities and estimated procurement costs.
- `GET /procurement/budget-check/{project_id}` - Cross-checks scheduled material procurement against remaining budget in Module 5, reporting any budget deficit.
