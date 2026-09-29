# Module 2: Equipment & Fleet Management

This module manages heavy machinery assets, fleet vehicles, equipment maintenance logs, and project booking allocations with double-booking conflict prevention.

## Database Tables
- `equipment` (ID prefix: `EQ-`, e.g., `EQ-0001`)
- `vehicles` (ID prefix: `VEH-`, e.g., `VEH-0001`)
- `maintenance_records` (ID prefix: `MNT-`, e.g., `MNT-0001`)
- `equipment_allocations` (ID prefix: `EA-`, e.g., `EA-0001`)
- `vehicle_allocations` (ID prefix: `VA-`, e.g., `VA-0001`)

## Endpoints

### Equipment
- `GET /equipment` - List all equipment (supports `?status=Available` and `?limit=100`)
- `GET /equipment/{equipment_id}` - Retrieve single equipment machine
- `POST /equipment` - Create equipment asset (auto-generates `EQ-xxxx`)
- `PATCH /equipment/{equipment_id}` - Partial update of equipment details
- `DELETE /equipment/{equipment_id}` - Delete equipment machine

### Fleet Vehicles
- `GET /vehicles` - List all fleet vehicles (supports `?status=Available` and `?limit=100`)
- `GET /vehicles/{vehicle_id}` - Retrieve single vehicle
- `POST /vehicles` - Register new vehicle (auto-generates `VEH-xxxx`)
- `PATCH /vehicles/{vehicle_id}` - Partial update of vehicle details
- `DELETE /vehicles/{vehicle_id}` - Delete vehicle

### Maintenance Records
- `GET /maintenance-records` (or `/maintenance`) - List maintenance records (supports `?equipment_id=EQ-0001`)
- `GET /maintenance-records/{maintenance_id}` (or `/maintenance/{id}`) - Get maintenance record
- `POST /maintenance-records` (or `/maintenance`) - Schedule maintenance log (auto-sets equipment status to `"Under Maintenance"`)
- `DELETE /maintenance-records/{maintenance_id}` (or `/maintenance/{id}`) - Delete maintenance record (restores equipment status to `"Available"` if no other active maintenance exists)

### Allocations (with double-booking conflict check)
- `GET /equipment-allocations` - List equipment allocations (supports `?project_id=...` and `?equipment_id=...`)
- `GET /equipment-allocations/{allocation_id}` - Get equipment allocation
- `POST /equipment-allocations` - Book equipment on project with date overlap conflict check (returns `409 Conflict` if double-booked)
- `PATCH /equipment-allocations/{allocation_id}` - Reschedule or reassign equipment allocation
- `PATCH /equipment-allocations/{allocation_id}/status` - Update allocation status (auto-releases equipment to `"Available"` if `"Cancelled"`)
- `DELETE /equipment-allocations/{allocation_id}` - Delete equipment allocation
- `GET /vehicle-allocations` - List vehicle allocations
- `GET /vehicle-allocations/{vehicle_allocation_id}` - Get vehicle allocation
- `POST /vehicle-allocations` - Allocate vehicle to project with date overlap check
- `PATCH /vehicle-allocations/{vehicle_allocation_id}` - Reschedule or reassign vehicle allocation
- `PATCH /vehicle-allocations/{vehicle_allocation_id}/status` - Update vehicle allocation status (auto-releases vehicle to `"Available"` if `"Cancelled"`)
- `DELETE /vehicle-allocations/{vehicle_allocation_id}` - Delete vehicle allocation
