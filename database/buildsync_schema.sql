-- =========================================================
-- BUILDSYNC DATABASE SCHEMA
-- Construction Management Resource System
-- =========================================================

-- 1. PROJECTS
CREATE TABLE projects (
    project_id VARCHAR(20) PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL,
    project_type VARCHAR(100),
    location VARCHAR(150),
    start_date DATE,
    end_date DATE,
    budget NUMERIC(15,2),
    priority VARCHAR(20),
    status VARCHAR(30),
    completion_percentage NUMERIC(5,2)
);


-- 2. EMPLOYEES
CREATE TABLE employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    position VARCHAR(100),
    skill VARCHAR(100),
    phone VARCHAR(30),
    employment_status VARCHAR(30),
    daily_rate NUMERIC(12,2)
);


-- 3. CONTRACTORS
CREATE TABLE contractors (
    contractor_id VARCHAR(20) PRIMARY KEY,
    contractor_name VARCHAR(150) NOT NULL,
    specialization VARCHAR(100),
    contact_person VARCHAR(150),
    phone VARCHAR(30),
    rating NUMERIC(3,2),
    status VARCHAR(30)
);


-- 4. EQUIPMENT
CREATE TABLE equipment (
    equipment_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(100),
    model VARCHAR(100),
    status VARCHAR(30),
    daily_rental_cost NUMERIC(12,2),
    purchase_value NUMERIC(15,2)
);


-- 5. VEHICLES
CREATE TABLE vehicles (
    vehicle_id VARCHAR(20) PRIMARY KEY,
    vehicle_type VARCHAR(100),
    plate_number VARCHAR(30) UNIQUE,
    driver VARCHAR(150),
    status VARCHAR(30),
    daily_operating_cost NUMERIC(12,2)
);


-- 6. MATERIALS
CREATE TABLE materials (
    material_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(100),
    unit VARCHAR(50),
    quantity_in_stock NUMERIC(12,2),
    reorder_level NUMERIC(12,2),
    unit_cost NUMERIC(12,2)
);


-- 7. SUPPLIERS
CREATE TABLE suppliers (
    supplier_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(150),
    phone VARCHAR(30),
    location VARCHAR(150),
    supplier_rating NUMERIC(3,2),
    status VARCHAR(30)
);


-- 8. PROJECT SCHEDULES
CREATE TABLE project_schedules (
    schedule_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    task_name VARCHAR(150) NOT NULL,
    start_date DATE,
    end_date DATE,
    duration_days INTEGER,
    dependency VARCHAR(100),
    status VARCHAR(30),

    CONSTRAINT fk_schedule_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE
);


-- 8a. RESOURCES ASSIGNED DIRECTLY TO TASKS
CREATE TABLE task_resource_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schedule_id VARCHAR(20) NOT NULL REFERENCES project_schedules(schedule_id) ON DELETE CASCADE,
    resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('employee', 'equipment', 'vehicle', 'material')),
    resource_id VARCHAR(20) NOT NULL,
    quantity NUMERIC(12,2) CHECK (quantity IS NULL OR quantity > 0),
    UNIQUE (schedule_id, resource_type, resource_id)
);


-- 9. EQUIPMENT ALLOCATIONS
CREATE TABLE equipment_allocations (
    allocation_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    equipment_id VARCHAR(20) NOT NULL,
    start_date DATE,
    end_date DATE,
    purpose VARCHAR(150),
    allocation_status VARCHAR(30),

    CONSTRAINT fk_equipment_allocation_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_equipment_allocation_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment(equipment_id)
        ON DELETE CASCADE
);


-- 10. EMPLOYEE ALLOCATIONS
CREATE TABLE employee_allocations (
    employee_allocation_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    employee_id VARCHAR(20) NOT NULL,
    start_date DATE,
    end_date DATE,
    role VARCHAR(100),
    allocation_status VARCHAR(30),

    CONSTRAINT fk_employee_allocation_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_employee_allocation_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE CASCADE
);


-- 11. MATERIAL ALLOCATIONS
CREATE TABLE material_allocations (
    material_allocation_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    material_id VARCHAR(20) NOT NULL,
    quantity_required NUMERIC(12,2),
    quantity_used NUMERIC(12,2),
    required_date DATE,
    status VARCHAR(30),

    CONSTRAINT fk_material_allocation_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_material_allocation_material
        FOREIGN KEY (material_id)
        REFERENCES materials(material_id)
        ON DELETE CASCADE
);


-- 11a. HISTORICAL MATERIAL DEMAND
CREATE TABLE historical_material_demand (
    demand_id VARCHAR(20) PRIMARY KEY,
    material_id VARCHAR(20) NOT NULL,
    demand_date DATE NOT NULL,
    quantity_demanded NUMERIC(12,2) NOT NULL,
    project_id VARCHAR(20),

    CONSTRAINT fk_historical_demand_material
        FOREIGN KEY (material_id)
        REFERENCES materials(material_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_historical_demand_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE SET NULL
);

-- Dated actual consumption observations used by material-demand forecasting.
CREATE TABLE material_consumption_history (
    consumption_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    material_id VARCHAR(20) NOT NULL REFERENCES materials(material_id) ON DELETE CASCADE,
    quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    consumed_on DATE NOT NULL
);


-- Dated actual costs used by project-cost forecasting.
CREATE TABLE project_cost_history (
    cost_entry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    incurred_on DATE NOT NULL,
    description VARCHAR(250)
);

-- 12. VEHICLE ALLOCATIONS
CREATE TABLE vehicle_allocations (
    vehicle_allocation_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    vehicle_id VARCHAR(20) NOT NULL,
    start_date DATE,
    end_date DATE,
    purpose VARCHAR(150),
    allocation_status VARCHAR(30),

    CONSTRAINT fk_vehicle_allocation_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_vehicle_allocation_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE CASCADE
);


-- 13. BUDGETS
CREATE TABLE budgets (
    budget_id VARCHAR(20) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    allocated_budget NUMERIC(15,2),
    labor_cost NUMERIC(15,2),
    material_cost NUMERIC(15,2),
    equipment_cost NUMERIC(15,2),
    actual_spending NUMERIC(15,2),
    remaining_budget NUMERIC(15,2),

    CONSTRAINT fk_budget_project
        FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE
);


-- 14. MAINTENANCE RECORDS
CREATE TABLE maintenance_records (
    maintenance_id VARCHAR(20) PRIMARY KEY,
    equipment_id VARCHAR(20) NOT NULL,
    maintenance_date DATE,
    maintenance_type VARCHAR(100),
    maintenance_cost NUMERIC(12,2),
    duration_days INTEGER,
    maintenance_status VARCHAR(30),

    CONSTRAINT fk_maintenance_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment(equipment_id)
        ON DELETE CASCADE
);


-- 15. ROLES
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(150)
);


-- 16. USERS
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_role
        FOREIGN KEY (role_id)
        REFERENCES roles(role_id)
        ON DELETE RESTRICT
);


-- =========================================================
-- INDEXES
-- These make searches and allocation checks faster.
-- =========================================================

CREATE INDEX idx_project_schedule_project
ON project_schedules(project_id);

CREATE INDEX idx_equipment_allocation_equipment
ON equipment_allocations(equipment_id);

CREATE INDEX idx_employee_allocation_employee
ON employee_allocations(employee_id);

CREATE INDEX idx_material_allocation_material
ON material_allocations(material_id);

CREATE INDEX idx_material_consumption_material_date
ON material_consumption_history(material_id, consumed_on);

CREATE INDEX idx_project_cost_history_project_date
ON project_cost_history(project_id, incurred_on);

CREATE INDEX idx_vehicle_allocation_vehicle
ON vehicle_allocations(vehicle_id);

CREATE INDEX idx_budget_project
ON budgets(project_id);

CREATE INDEX idx_maintenance_equipment
ON maintenance_records(equipment_id);

CREATE INDEX idx_user_employee
ON users(employee_id);

CREATE INDEX idx_user_role
ON users(role_id);

CREATE INDEX idx_historical_demand_material
ON historical_material_demand(material_id);

CREATE INDEX idx_historical_demand_date
ON historical_material_demand(demand_date);