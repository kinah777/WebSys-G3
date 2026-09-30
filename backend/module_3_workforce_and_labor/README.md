# Module 3: Workforce & Labor Management

This module manages internal staff and labor records, subcontracted trade firms, worker assignment allocations with conflict checking, and available worker search.

## Database Tables
- `employees` (ID prefix: `EMP-`, e.g., `EMP-0001`)
- `contractors` (ID prefix: `CON-`, e.g., `CON-0001`)
- `employee_allocations` (ID prefix: `EMPA-`, e.g., `EMPA-0001`)

## Endpoints

### Employees
- `GET /employees` - List employees (supports `?status=Active`, `?skill=Carpentry`, and `?limit=100`)
- `GET /employees/{employee_id}` - Retrieve employee details
- `POST /employees` - Register employee (auto-generates `EMP-xxxx`)
- `PATCH /employees/{employee_id}` - Partial update of employee details
- `DELETE /employees/{employee_id}` - Delete employee record

### Contractors
- `GET /contractors` - List external contractors (supports `?status=Active` and `?limit=100`)
- `GET /contractors/{contractor_id}` - Retrieve contractor details
- `POST /contractors` - Register contractor (auto-generates `CON-xxxx`)
- `PATCH /contractors/{contractor_id}` - Partial update of contractor details
- `DELETE /contractors/{contractor_id}` - Delete contractor record

### Allocations (with double-booking conflict check)
- `GET /employee-allocations` - List employee allocations (supports `?project_id=...` and `?employee_id=...`)
- `GET /employee-allocations/{employee_allocation_id}` - Get single allocation
- `POST /employee-allocations` - Assign worker to project with date overlap conflict check (returns `409 Conflict` if already booked)
- `PATCH /employee-allocations/{employee_allocation_id}` - Reschedule or reassign worker
- `PATCH /employee-allocations/{employee_allocation_id}/status` - Update allocation status (`Scheduled`, `Active`, `Completed`, `Cancelled`)
- `DELETE /employee-allocations/{employee_allocation_id}` - Delete allocation

### Complex Endpoints
- `GET /employees/available/search?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&skill=Trade` - Finds all active employees with zero schedule overlaps during the target window, filtered by trade skill.
