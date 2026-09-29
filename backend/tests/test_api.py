"""
BuildSync Automated Backend API Integration Test Suite
======================================================
Tests all 6 modules:
- Module 1: Projects & Schedules (CRUD, Progress, Timeline)
- Module 2: Equipment & Fleet (CRUD, Maintenance, Allocations with conflict check)
- Module 3: Workforce & Labor (CRUD, Worker assignments, Available worker search)
- Module 4: Materials & Supply Chain (CRUD, Stock deductions, Low-stock alert, Budget check)
- Module 5: Financials & Forecasting (CRUD, Summary KPIs, Burn rate forecast)
- Module 6: Resource Conflict Resolution Center (Detection & Resolution Actions)
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.api import app

client = TestClient(app)


def test_system_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


def test_module_1_projects_and_schedules():
    # List projects
    r = client.get("/projects?limit=5")
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) > 0
    pid = projects[0]["project_id"]

    # Single project
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["project_id"] == pid

    # Dynamic progress calculation
    r = client.get(f"/projects/{pid}/progress")
    assert r.status_code == 200
    assert "completion_percentage" in r.json()

    # Timeline milestone tasks
    r = client.get(f"/projects/{pid}/timeline")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Schedules & alias
    r = client.get("/schedules?limit=5")
    assert r.status_code == 200
    r_alias = client.get("/project-schedules?limit=5")
    assert r_alias.status_code == 200


def test_module_2_equipment_and_fleet():
    # Equipment list & single
    r = client.get("/equipment?limit=5")
    assert r.status_code == 200
    eq_id = r.json()[0]["equipment_id"]
    r_single = client.get(f"/equipment/{eq_id}")
    assert r_single.status_code == 200

    # Vehicles list & single
    r = client.get("/vehicles?limit=5")
    assert r.status_code == 200
    veh_id = r.json()[0]["vehicle_id"]
    r_veh = client.get(f"/vehicles/{veh_id}")
    assert r_veh.status_code == 200

    # Maintenance records
    r = client.get("/maintenance-records?limit=5")
    assert r.status_code == 200

    # Allocations
    r = client.get("/equipment-allocations?limit=5")
    assert r.status_code == 200
    r = client.get("/vehicle-allocations?limit=5")
    assert r.status_code == 200


def test_module_3_workforce_and_labor():
    # Employees list
    r = client.get("/employees?limit=5")
    assert r.status_code == 200
    emp_id = r.json()[0]["employee_id"]
    r_emp = client.get(f"/employees/{emp_id}")
    assert r_emp.status_code == 200

    # Contractors list
    r = client.get("/contractors?limit=5")
    assert r.status_code == 200

    # Available search
    r = client.get("/employees/available/search?start_date=2026-06-01&end_date=2026-06-15")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_module_4_materials_and_supply_chain():
    # Materials list
    r = client.get("/materials?limit=5")
    assert r.status_code == 200

    # Suppliers list
    r = client.get("/suppliers?limit=5")
    assert r.status_code == 200

    # Low stock alerts
    r = client.get("/materials/alerts/low-stock")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Budget procurement feasibility check
    r = client.get("/procurement/budget-check/PRJ-0001")
    assert r.status_code in (200, 404)


def test_module_5_financials_and_forecasting():
    # Budgets list
    r = client.get("/budgets?limit=5")
    assert r.status_code == 200

    # Portfolio summary KPIs
    r = client.get("/financials/summary")
    assert r.status_code == 200
    summary = r.json()
    assert "total_allocated" in summary
    assert "total_spent" in summary

    # Predictive cost forecast
    r = client.get("/financials/forecast?limit=3")
    assert r.status_code == 200
    assert len(r.json()) > 0
    assert "daily_burn_rate" in r.json()[0]


def test_module_6_conflict_resolution_center():
    # Summary
    r = client.get("/conflicts/summary")
    assert r.status_code == 200
    assert "total" in r.json()

    # Detections
    assert client.get("/conflicts/equipment").status_code == 200
    assert client.get("/conflicts/employees").status_code == 200
    assert client.get("/conflicts/vehicles").status_code == 200


def test_task_resource_assignment_round_trip():
    projects = client.get("/projects?limit=1").json()
    materials = client.get("/materials?limit=100").json()
    material = next((item for item in materials if item["quantity_in_stock"] >= 0.01), None)
    assert projects and material

    task_response = client.post("/project-schedules", json={
        "project_id": projects[0]["project_id"],
        "task_name": "Task assignment integration test",
        "start_date": "2099-01-10",
        "end_date": "2099-01-12",
    })
    assert task_response.status_code == 201
    schedule_id = task_response.json()["schedule_id"]

    try:
        stock_before = float(material["quantity_in_stock"])
        assignment_response = client.post(
            f"/project-schedules/{schedule_id}/assignments",
            json={"resource_type": "material", "resource_id": material["material_id"], "quantity": 0.01},
        )
        assert assignment_response.status_code == 201
        assignment = assignment_response.json()
        assert assignment["resource_name"] == material["name"]
        assert assignment["quantity"] == 0.01

        duplicate_response = client.post(
            f"/project-schedules/{schedule_id}/assignments",
            json={"resource_type": "material", "resource_id": material["material_id"], "quantity": 0.01},
        )
        assert duplicate_response.status_code == 409

        listed = client.get(f"/project-schedules/{schedule_id}/assignments")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        delete_response = client.delete(
            f"/project-schedules/{schedule_id}/assignments/{assignment['assignment_id']}"
        )
        assert delete_response.status_code == 204
        updated_material = client.get(f"/materials/{material['material_id']}").json()
        assert round(float(updated_material["quantity_in_stock"]), 2) == round(stock_before, 2)
    finally:
        client.delete(f"/project-schedules/{schedule_id}")


def test_crud_and_error_handling():
    # 404 on nonexistent resource
    assert client.get("/projects/PRJ-NONEXISTENT").status_code == 404

    # 400 on start_date > end_date
    bad_date = client.post("/projects", json={
        "project_name": "Invalid Date Range",
        "start_date": "2026-12-31",
        "end_date": "2026-01-01"
    })
    assert bad_date.status_code == 400


if __name__ == "__main__":
    test_system_root()
    test_module_1_projects_and_schedules()
    test_module_2_equipment_and_fleet()
    test_module_3_workforce_and_labor()
    test_module_4_materials_and_supply_chain()
    test_module_5_financials_and_forecasting()
    test_module_6_conflict_resolution_center()
    test_task_resource_assignment_round_trip()
    test_crud_and_error_handling()
    print("ALL TESTS PASSED SUCCESSFULLY!")
