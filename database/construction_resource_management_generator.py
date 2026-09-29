import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

# ============================================================
# CONSTRUCTION COMPANY RESOURCE MANAGEMENT SYSTEM
# Synthetic Dataset Generator
# 500 records per table
# ============================================================

fake = Faker()
random.seed(42)
Faker.seed(42)

OUTPUT_DIR = "construction_resource_management_dataset"
os.makedirs(OUTPUT_DIR, exist_ok=True)

N = 500

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

first_names = [
    "James", "John", "Michael", "Robert", "David", "Daniel", "Mark",
    "Anthony", "Joseph", "Christopher", "Matthew", "Andrew", "Joshua",
    "William", "Kevin", "Brian", "Carlos", "Miguel", "Jose", "Angel"
]

last_names = [
    "Santos", "Reyes", "Cruz", "Garcia", "Dela Cruz", "Mendoza",
    "Bautista", "Ramos", "Torres", "Flores", "Navarro", "Castillo",
    "Rivera", "Gonzales", "Aquino", "Villanueva", "Fernandez"
]

project_types = [
    "Residential Building", "Commercial Building", "Road Construction",
    "Bridge Construction", "Warehouse", "School Building",
    "Hospital", "Office Building", "Renovation", "Drainage Project"
]

project_statuses = ["Planning", "Ongoing", "On Hold", "Completed"]

positions = [
    "Project Manager", "Site Engineer", "Civil Engineer",
    "Architect", "Foreman", "Electrician", "Plumber",
    "Mason", "Carpenter", "Heavy Equipment Operator",
    "Safety Officer", "Surveyor", "Welder", "Laborer"
]

skills = [
    "Project Management", "Civil Works", "Electrical",
    "Plumbing", "Masonry", "Carpentry", "Heavy Equipment",
    "Welding", "Surveying", "Safety Management"
]

equipment_types = [
    "Excavator", "Bulldozer", "Crane", "Backhoe Loader",
    "Concrete Mixer", "Road Roller", "Forklift", "Loader",
    "Generator", "Compactor"
]

vehicle_types = [
    "Dump Truck", "Pickup Truck", "Concrete Mixer Truck",
    "Flatbed Truck", "Service Van", "Water Truck",
    "Fuel Truck", "Delivery Truck"
]

material_types = [
    "Cement", "Steel", "Gravel", "Sand", "Concrete",
    "Lumber", "Bricks", "Paint", "Pipes", "Electrical Supplies"
]

supplier_names = [
    "BuildPro Supplies", "Prime Construction Supply",
    "Metro Builders Depot", "SolidCore Materials",
    "Pacific Construction Trading", "Golden Hammer Supply",
    "Reliable Builders Inc.", "Stronghold Materials",
    "Central Hardware Supply", "Alpha Construction Trading"
]

philippine_cities = [
    "Manila", "Quezon City", "Makati", "Pasig", "Taguig",
    "Cavite City", "Imus", "Dasmarinas", "Bacoor",
    "Santa Rosa", "Biñan", "Calamba", "Antipolo", "Laguna"
]

start_date = date(2026, 1, 1)

def random_date(start=start_date, days=730):
    return start + timedelta(days=random.randint(0, days))

def random_end_date(start, min_days=3, max_days=60):
    return start + timedelta(days=random.randint(min_days, max_days))

def money(minimum, maximum):
    return round(random.uniform(minimum, maximum), 2)

def random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"


# ============================================================
# 1. PROJECTS
# ============================================================

projects = []

for i in range(1, N + 1):
    project_start = random_date()
    project_end = random_end_date(project_start, 30, 365)

    projects.append({
        "project_id": f"PRJ-{i:04d}",
        "project_name": f"{random.choice(project_types)} Project {i:03d}",
        "project_type": random.choice(project_types),
        "location": random.choice(philippine_cities),
        "start_date": project_start,
        "end_date": project_end,
        "budget": money(500_000, 50_000_000),
        "priority": random.choice(["Low", "Medium", "High", "Critical"]),
        "status": random.choice(project_statuses),
        "completion_percentage": random.randint(0, 100)
    })

projects_df = pd.DataFrame(projects)


# ============================================================
# 2. EMPLOYEES
# ============================================================

employees = []

for i in range(1, N + 1):
    employees.append({
        "employee_id": f"EMP-{i:04d}",
        "name": random_name(),
        "position": random.choice(positions),
        "skill": random.choice(skills),
        "phone": f"09{random.randint(100000000, 999999999)}",
        "employment_status": random.choice(["Active", "Active", "Active", "On Leave"]),
        "daily_rate": money(500, 5000)
    })

employees_df = pd.DataFrame(employees)


# ============================================================
# 3. CONTRACTORS
# ============================================================

contractors = []

for i in range(1, N + 1):
    contractors.append({
        "contractor_id": f"CON-{i:04d}",
        "contractor_name": f"{random.choice(['ABC', 'Prime', 'Metro', 'Global', 'Pacific', 'Solid'])} "
                           f"{random.choice(['Builders', 'Construction', 'Contracting', 'Engineering'])} {i:03d}",
        "specialization": random.choice([
            "General Construction", "Electrical", "Plumbing",
            "Structural Works", "Road Works", "Painting",
            "Equipment Rental", "Concrete Works"
        ]),
        "contact_person": random_name(),
        "phone": f"09{random.randint(100000000, 999999999)}",
        "rating": round(random.uniform(3.0, 5.0), 1),
        "status": random.choice(["Active", "Active", "Inactive"])
    })

contractors_df = pd.DataFrame(contractors)


# ============================================================
# 4. EQUIPMENT
# ============================================================

equipment = []

for i in range(1, N + 1):
    equipment.append({
        "equipment_id": f"EQ-{i:04d}",
        "name": f"{random.choice(equipment_types)} {i:03d}",
        "type": random.choice(equipment_types),
        "model": f"Model-{random.randint(2018, 2026)}-{random.randint(100, 999)}",
        "status": random.choice(["Available", "Available", "In Use", "Maintenance"]),
        "daily_rental_cost": money(2000, 50000),
        "purchase_value": money(100_000, 15_000_000)
    })

equipment_df = pd.DataFrame(equipment)


# ============================================================
# 5. VEHICLES
# ============================================================

vehicles = []

for i in range(1, N + 1):
    vehicles.append({
        "vehicle_id": f"VEH-{i:04d}",
        "vehicle_type": random.choice(vehicle_types),
        "plate_number": f"{random.choice(['ABC', 'XYZ', 'NDE', 'JKS'])}-{random.randint(1000, 9999)}",
        "driver": random_name(),
        "status": random.choice(["Available", "Available", "In Use", "Maintenance"]),
        "daily_operating_cost": money(1000, 15000)
    })

vehicles_df = pd.DataFrame(vehicles)


# ============================================================
# 6. MATERIALS
# ============================================================

materials = []

for i in range(1, N + 1):
    material = random.choice(material_types)

    materials.append({
        "material_id": f"MAT-{i:04d}",
        "name": f"{material} Grade {random.choice(['A', 'B', 'C'])} {i:03d}",
        "type": material,
        "unit": random.choice(["kg", "bags", "tons", "pcs", "meters", "liters"]),
        "quantity_in_stock": random.randint(50, 10000),
        "reorder_level": random.randint(20, 1000),
        "unit_cost": money(10, 5000)
    })

materials_df = pd.DataFrame(materials)


# ============================================================
# 7. SUPPLIERS
# ============================================================

suppliers = []

for i in range(1, N + 1):
    suppliers.append({
        "supplier_id": f"SUP-{i:04d}",
        "name": f"{random.choice(supplier_names)} {i:03d}",
        "contact_person": random_name(),
        "phone": f"09{random.randint(100000000, 999999999)}",
        "location": random.choice(philippine_cities),
        "supplier_rating": round(random.uniform(3.0, 5.0), 1),
        "status": random.choice(["Active", "Active", "Inactive"])
    })

suppliers_df = pd.DataFrame(suppliers)


# ============================================================
# 8. PROJECT SCHEDULES
# ============================================================

tasks = [
    "Site Preparation", "Excavation", "Foundation",
    "Structural Framing", "Concrete Works", "Electrical Installation",
    "Plumbing Installation", "Roofing", "Painting",
    "Finishing", "Inspection", "Site Cleanup"
]

project_schedules = []

for i in range(1, N + 1):
    project = random.choice(projects)
    task_start = project["start_date"] + timedelta(days=random.randint(0, 100))
    task_end = random_end_date(task_start, 1, 30)

    project_schedules.append({
        "schedule_id": f"SCH-{i:04d}",
        "project_id": project["project_id"],
        "task_name": random.choice(tasks),
        "start_date": task_start,
        "end_date": task_end,
        "duration_days": (task_end - task_start).days + 1,
        "dependency": random.choice(["None", "Previous Task", "Foundation", "Excavation"]),
        "status": random.choice(["Not Started", "In Progress", "Completed"])
    })

project_schedules_df = pd.DataFrame(project_schedules)


# ============================================================
# 9. EQUIPMENT ALLOCATIONS
# ============================================================

equipment_allocations = []

for i in range(1, N + 1):
    project = random.choice(projects)
    eq = random.choice(equipment)

    allocation_start = project["start_date"] + timedelta(days=random.randint(0, 60))
    allocation_end = random_end_date(allocation_start, 2, 20)

    equipment_allocations.append({
        "allocation_id": f"EA-{i:04d}",
        "project_id": project["project_id"],
        "equipment_id": eq["equipment_id"],
        "start_date": allocation_start,
        "end_date": allocation_end,
        "purpose": random.choice(tasks),
        "allocation_status": random.choice(["Scheduled", "Active", "Completed"])
    })

# Deliberately create clear equipment conflicts
conflict_equipment = "EQ-0001"

equipment_allocations[0] = {
    "allocation_id": "EA-0001",
    "project_id": "PRJ-0001",
    "equipment_id": conflict_equipment,
    "start_date": date(2026, 1, 10),
    "end_date": date(2026, 1, 15),
    "purpose": "Excavation",
    "allocation_status": "Scheduled"
}

equipment_allocations[1] = {
    "allocation_id": "EA-0002",
    "project_id": "PRJ-0002",
    "equipment_id": conflict_equipment,
    "start_date": date(2026, 1, 13),
    "end_date": date(2026, 1, 20),
    "purpose": "Site Preparation",
    "allocation_status": "Scheduled"
}

equipment_allocations_df = pd.DataFrame(equipment_allocations)


# ============================================================
# 10. EMPLOYEE ALLOCATIONS
# ============================================================

employee_allocations = []

for i in range(1, N + 1):
    project = random.choice(projects)
    employee = random.choice(employees)

    allocation_start = project["start_date"] + timedelta(days=random.randint(0, 60))
    allocation_end = random_end_date(allocation_start, 2, 30)

    employee_allocations.append({
        "employee_allocation_id": f"EMPA-{i:04d}",
        "project_id": project["project_id"],
        "employee_id": employee["employee_id"],
        "start_date": allocation_start,
        "end_date": allocation_end,
        "role": employee["position"],
        "allocation_status": random.choice(["Scheduled", "Active", "Completed"])
    })

employee_allocations_df = pd.DataFrame(employee_allocations)


# ============================================================
# 11. MATERIAL ALLOCATIONS
# ============================================================

material_allocations = []

for i in range(1, N + 1):
    project = random.choice(projects)
    material = random.choice(materials)

    quantity = random.randint(10, 5000)

    material_allocations.append({
        "material_allocation_id": f"MA-{i:04d}",
        "project_id": project["project_id"],
        "material_id": material["material_id"],
        "quantity_required": quantity,
        "quantity_used": random.randint(0, quantity),
        "required_date": project["start_date"] + timedelta(days=random.randint(0, 100)),
        "status": random.choice(["Pending", "Ordered", "Delivered", "Used"])
    })

material_allocations_df = pd.DataFrame(material_allocations)


# ============================================================
# 12. VEHICLE ALLOCATIONS
# ============================================================

vehicle_allocations = []

for i in range(1, N + 1):
    project = random.choice(projects)
    vehicle = random.choice(vehicles)

    allocation_start = project["start_date"] + timedelta(days=random.randint(0, 60))
    allocation_end = random_end_date(allocation_start, 2, 20)

    vehicle_allocations.append({
        "vehicle_allocation_id": f"VA-{i:04d}",
        "project_id": project["project_id"],
        "vehicle_id": vehicle["vehicle_id"],
        "start_date": allocation_start,
        "end_date": allocation_end,
        "purpose": random.choice(tasks),
        "allocation_status": random.choice(["Scheduled", "Active", "Completed"])
    })

# Deliberately create a clear vehicle conflict
conflict_vehicle = "VEH-0001"

vehicle_allocations[0] = {
    "vehicle_allocation_id": "VA-0001",
    "project_id": "PRJ-0001",
    "vehicle_id": conflict_vehicle,
    "start_date": date(2026, 1, 10),
    "end_date": date(2026, 1, 15),
    "purpose": "Material Delivery",
    "allocation_status": "Scheduled"
}

vehicle_allocations[1] = {
    "vehicle_allocation_id": "VA-0002",
    "project_id": "PRJ-0002",
    "vehicle_id": conflict_vehicle,
    "start_date": date(2026, 1, 13),
    "end_date": date(2026, 1, 20),
    "purpose": "Equipment Transport",
    "allocation_status": "Scheduled"
}

vehicle_allocations_df = pd.DataFrame(vehicle_allocations)


# ============================================================
# 13. BUDGETS
# ============================================================

budgets = []

for i in range(1, N + 1):
    project = projects[i - 1]

    budget = project["budget"]
    spent = round(random.uniform(0.1, 1.1) * budget, 2)

    budgets.append({
        "budget_id": f"BUD-{i:04d}",
        "project_id": project["project_id"],
        "allocated_budget": budget,
        "labor_cost": money(50_000, budget * 0.4),
        "material_cost": money(50_000, budget * 0.4),
        "equipment_cost": money(20_000, budget * 0.2),
        "actual_spending": spent,
        "remaining_budget": round(budget - spent, 2)
    })

budgets_df = pd.DataFrame(budgets)


# ============================================================
# 14. MAINTENANCE RECORDS
# ============================================================

maintenance = []

for i in range(1, N + 1):
    equipment_item = random.choice(equipment)
    maintenance_date = random_date()

    maintenance.append({
        "maintenance_id": f"MAIN-{i:04d}",
        "equipment_id": equipment_item["equipment_id"],
        "maintenance_date": maintenance_date,
        "maintenance_type": random.choice([
            "Routine Inspection", "Oil Change", "Repair",
            "Engine Service", "Parts Replacement", "Safety Inspection"
        ]),
        "maintenance_cost": money(1000, 100000),
        "duration_days": random.randint(1, 7),
        "maintenance_status": random.choice(["Scheduled", "Completed", "In Progress"])
    })

maintenance_df = pd.DataFrame(maintenance)


# ============================================================
# SAVE ALL DATASETS
# ============================================================

datasets = {
    "projects.csv": projects_df,
    "employees.csv": employees_df,
    "contractors.csv": contractors_df,
    "equipment.csv": equipment_df,
    "vehicles.csv": vehicles_df,
    "materials.csv": materials_df,
    "suppliers.csv": suppliers_df,
    "project_schedules.csv": project_schedules_df,
    "equipment_allocations.csv": equipment_allocations_df,
    "employee_allocations.csv": employee_allocations_df,
    "material_allocations.csv": material_allocations_df,
    "vehicle_allocations.csv": vehicle_allocations_df,
    "budgets.csv": budgets_df,
    "maintenance_records.csv": maintenance_df
}

for filename, dataframe in datasets.items():
    dataframe.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)

print("=" * 60)
print("CONSTRUCTION RESOURCE MANAGEMENT DATASET GENERATED")
print()
print("Intentional vehicle conflict:")
print("  VEH-0001")
print("  PRJ-0001 → January 10–15, 2026")
print("  PRJ-0002 → January 13–20, 2026")
print("  Conflict period → January 13–15, 2026")
print("=" * 60)
print(f"Output folder: {os.path.abspath(OUTPUT_DIR)}")
print(f"Records per table: {N}")
print(f"Number of tables: {len(datasets)}")
print(f"Total records: {N * len(datasets):,}")
print()
print("Files created:")

for filename, dataframe in datasets.items():
    print(f"  ✓ {filename:<35} {len(dataframe)} records")

print()
print("Intentional equipment conflict:")
print("  EQ-0001 / Excavator")
print("  PRJ-0001 → January 10–15, 2026")
print("  PRJ-0002 → January 13–20, 2026")
print("  Conflict period → January 13–15, 2026")
print("=" * 60)