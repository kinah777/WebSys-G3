# Module 6: Resource Conflict Resolution Center

The central cross-cutting operational engine of BuildSync:
- Detects overlapping date ranges for physical resources across projects (Equipment, Workforce, and Fleet Vehicles).
- Provides resolution action endpoints (Cancel, Reschedule, Reassign).

## Conflict Overlap Rule
Two bookings overlap when: `(a.start <= b.end) AND (a.end >= b.start)` where status is not `Completed` or `Cancelled`.

## Endpoints

### Detection Endpoints
- `GET /conflicts/equipment` - Returns all conflicting pairs of equipment allocations where the same machine is double-booked.
- `GET /conflicts/employees` - Returns all conflicting pairs of employee allocations where the same worker is double-booked.
- `GET /conflicts/vehicles` - Returns all conflicting pairs of vehicle allocations where the same fleet vehicle is double-booked.
- `GET /conflicts/summary` - Returns badge counters: `{ equipment, employees, vehicles, total }`.

### Resolution Action Endpoints
- `POST /conflicts/resolve/cancel` - Cancels one of the conflicting allocations and frees up the physical asset.
  - Body: `{ "allocation_type": "equipment" | "employee" | "vehicle", "allocation_id": "EA-0001" }`
- `POST /conflicts/resolve/reschedule` - Adjusts dates of an allocation to clear the conflict, validating that new dates do not create another conflict.
  - Body: `{ "allocation_type": "equipment", "allocation_id": "EA-0001", "new_start_date": "2026-02-01", "new_end_date": "2026-02-10" }`
- `POST /conflicts/resolve/reassign` - Reassigns allocation to a different replacement resource, checking availability.
  - Body: `{ "allocation_type": "equipment", "allocation_id": "EA-0001", "new_resource_id": "EQ-0002" }`
