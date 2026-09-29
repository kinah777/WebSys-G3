````markdown
# BuildSync Database

This folder contains the database resources for **BuildSync - Construction Management Resource System**.

The database uses **PostgreSQL** and can be hosted using **Neon PostgreSQL** or run using a local PostgreSQL installation.

---

# Database Overview

The BuildSync database contains:

- **14 tables**
- **500 records per table**
- **7,000 total records**

The database supports the following major system functions:

- Project management
- Task and project scheduling
- Employee management
- Contractor management
- Equipment management
- Vehicle management
- Material and inventory management
- Supplier management
- Resource allocation
- Budget tracking
- Equipment maintenance
- Resource conflict detection
- Data preparation for analytics

---

# Database Structure

The database contains the following 14 tables:

| # | Table | Description |
|---|---|---|
| 1 | `projects` | Stores construction project information |
| 2 | `employees` | Stores employee and worker information |
| 3 | `contractors` | Stores contractor information |
| 4 | `equipment` | Stores construction equipment information |
| 5 | `vehicles` | Stores vehicle information |
| 6 | `materials` | Stores construction materials and inventory information |
| 7 | `suppliers` | Stores supplier information |
| 8 | `project_schedules` | Stores project tasks and schedules |
| 9 | `equipment_allocations` | Records equipment assigned to projects |
| 10 | `employee_allocations` | Records employees assigned to projects |
| 11 | `material_allocations` | Records materials required and used by projects |
| 12 | `vehicle_allocations` | Records vehicles assigned to projects |
| 13 | `budgets` | Stores project budget and spending information |
| 14 | `maintenance_records` | Stores equipment maintenance records |

---

# Folder Contents

```text
database/
│
├── construction_resource_management_dataset/
│   ├── projects.csv
│   ├── employees.csv
│   ├── contractors.csv
│   ├── equipment.csv
│   ├── vehicles.csv
│   ├── materials.csv
│   ├── suppliers.csv
│   ├── project_schedules.csv
│   ├── equipment_allocations.csv
│   ├── employee_allocations.csv
│   ├── material_allocations.csv
│   ├── vehicle_allocations.csv
│   ├── budgets.csv
│   └── maintenance_records.csv
│
├── buildsync_schema.sql
├── construction_resource_management_generator.py
├── import_data.py
├── README.md
└── .gitignore
````

---

# Dataset

The finalized dataset is stored in:

```text
construction_resource_management_dataset/
```

Each CSV file contains **500 records**.

The dataset contains information related to:

* Construction projects
* Employees
* Contractors
* Equipment
* Vehicles
* Materials
* Suppliers
* Project schedules
* Equipment allocations
* Employee allocations
* Material allocations
* Vehicle allocations
* Budgets
* Maintenance records

The finalized dataset contains **7,000 records in total** across the 14 tables.

---

# Database Schema

The PostgreSQL database schema is provided in:

```text
buildsync_schema.sql
```

This file creates the 14 BuildSync tables, their foreign key relationships, and the required indexes.

The schema should be created **before importing the CSV dataset** when setting up a new or empty database.

---

# Requirements

Before setting up the database, make sure you have:

* Python 3
* Git
* PostgreSQL or access to the shared Neon PostgreSQL database

The Python packages required by the database scripts are:

```text
psycopg[binary]
python-dotenv
```

---

# Setup

## 1. Clone the Repository

If you have not cloned the project yet:

```bash
git clone YOUR_REPOSITORY_URL
```

Then enter the project folder:

```bash
cd WebSys-G3
```

---

## 2. Create a Python Virtual Environment

From the project root, run:

```powershell
py -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your terminal should show:

```text
(.venv)
```

---

## 3. Install the Required Packages

Run:

```powershell
python -m pip install "psycopg[binary]" python-dotenv
```

---

# Using Neon PostgreSQL

The BuildSync project uses **Neon PostgreSQL** as the shared hosted database.

This allows team members to connect to the same PostgreSQL database without installing PostgreSQL locally.

---

## 1. Get the Neon Connection String

Open the BuildSync project in Neon.

Select:

**Connect**

Copy the PostgreSQL connection string.

It will look similar to:

```text
postgresql://username:password@host/database?sslmode=require
```

Do not use the example above as your actual connection string.

---

## 2. Create the `.env` File

Inside the `database` folder, create a file named:

```text
.env
```

The structure should be:

```text
database/
├── .env
├── buildsync_schema.sql
├── import_data.py
├── README.md
└── ...
```

Inside `.env`, add:

```env
DATABASE_URL=YOUR_NEON_CONNECTION_STRING
```

Replace `YOUR_NEON_CONNECTION_STRING` with the actual Neon connection string.

Example format:

```env
DATABASE_URL=postgresql://username:password@ep-example.neon.tech/neondb?sslmode=require
```

---

## 3. Keep `.env` Private

Do not upload or commit `.env` to GitHub.

The `.env` file contains database credentials.

Each team member should create their own local `.env` file.

The `.env` file should remain on the developer's computer.

---

# Important: Shared Neon Database

The shared Neon database has already been populated with the finalized BuildSync dataset.

It currently contains:

```text
14 tables
500 records per table
7,000 total records
```

Therefore, if you are connecting to the **existing shared Neon database**, you do **not** need to run the database schema or CSV import again.

You only need to:

1. Clone or pull the repository.
2. Create your virtual environment.
3. Install the required packages.
4. Create `database/.env`.
5. Add the shared Neon `DATABASE_URL`.
6. Run the backend/application.

The backend can then connect to the existing database.

---

# Creating a New BuildSync Database

If you are creating a **new or empty PostgreSQL/Neon database**, follow these steps.

```text
Create PostgreSQL/Neon Database
          ↓
Run buildsync_schema.sql
          ↓
14 tables created
          ↓
Configure database/.env
          ↓
Run import_data.py
          ↓
7,000 records imported
          ↓
Database ready
```

---

## Step 1: Create the Database

Create a new PostgreSQL database using either:

* Neon PostgreSQL
* Local PostgreSQL

---

## Step 2: Create the Database Schema

Open:

```text
buildsync_schema.sql
```

Run the complete SQL script in the PostgreSQL or Neon SQL Editor.

The script creates:

* 14 tables
* Primary keys
* Foreign key relationships
* Required indexes

The 14 tables are:

```text
projects
employees
contractors
equipment
vehicles
materials
suppliers
project_schedules
equipment_allocations
employee_allocations
material_allocations
vehicle_allocations
budgets
maintenance_records
```

---

## Step 3: Configure `.env`

Inside:

```text
database/.env
```

add:

```env
DATABASE_URL=YOUR_DATABASE_CONNECTION_STRING
```

Use the connection string for the new database.

---

## Step 4: Import the Dataset

Open the terminal inside the `database` folder:

```powershell
cd database
```

Run:

```powershell
python import_data.py
```

The script will read the CSV files from:

```text
construction_resource_management_dataset/
```

and insert the records into the PostgreSQL database.

---

# Import Order

The import script loads the CSV files in the following order:

```text
1. projects.csv
2. employees.csv
3. contractors.csv
4. equipment.csv
5. vehicles.csv
6. materials.csv
7. suppliers.csv
8. project_schedules.csv
9. equipment_allocations.csv
10. employee_allocations.csv
11. material_allocations.csv
12. vehicle_allocations.csv
13. budgets.csv
14. maintenance_records.csv
```

The order is important because some tables contain references to records in other tables.

For example:

```text
projects
   ↓
project_schedules
   ↓
resource allocations
```

---

# Import Result

A successful import should result in:

```text
14 tables
500 records per table
7,000 total records
```

The exact terminal output may vary depending on the version of the import script.

The important result is that all 14 CSV files are successfully imported into their corresponding PostgreSQL tables.

---

# Important: Do Not Run the Import Twice

The dataset is designed to populate an empty database.

Running the import script multiple times on the same database may cause:

* Duplicate primary key errors
* Duplicate unique-value errors
* Foreign key conflicts

If the shared Neon database is already populated, **do not run `import_data.py` again**.

If an import fails, check the error message before attempting another import.

---

# Dataset Generator

The file:

```text
construction_resource_management_generator.py
```

is the Python script used to generate the construction resource management dataset.

It can be used when the team needs to regenerate or create a new dataset.

Before replacing the existing dataset, make sure that:

1. The table names remain the same.
2. The CSV column names remain compatible with the PostgreSQL schema.
3. Required IDs and relationships are preserved.
4. Unique fields remain unique.
5. Foreign-key values correspond to existing records.
6. The generated data remains compatible with `import_data.py`.

The finalized CSV dataset should be used for the current BuildSync project unless the team agrees to generate a new version.

---

# Database Import Flow

The database setup follows this general flow:

```text
Dataset Generator
       ↓
CSV Dataset
       ↓
buildsync_schema.sql
       ↓
PostgreSQL Tables
       ↓
import_data.py
       ↓
PostgreSQL Database
       ↓
FastAPI Backend
       ↓
React Frontend
```

The CSV files are used to populate the PostgreSQL database.

The BuildSync application should communicate with PostgreSQL through the backend API rather than directly reading the CSV files.

---

# Team Development

For the shared BuildSync project, team members can connect their local development environment to the same Neon PostgreSQL database.

Each developer should:

1. Pull the latest repository changes.
2. Create their own local `.env` file.
3. Add the shared Neon `DATABASE_URL`.
4. Install the required Python packages.
5. Run the backend locally.
6. Connect the backend to the PostgreSQL database.

The shared database remains hosted in Neon.

Example:

```text
Developer A
    │
    ├── Local Backend
    │
    └── Local .env
             │
             ↓
       Neon PostgreSQL
             ↑
             │
    Local .env
    └── Developer B
```

---

# Security

Never commit or share:

```text
.env
```

Do not place database passwords or complete PostgreSQL connection strings in:

* GitHub source files
* README files
* Screenshots
* Public messages
* Public documentation
* Frontend JavaScript files

Database credentials should remain private.

The database connection should be handled by the backend/server side.

---

# Troubleshooting

## `DATABASE_URL was not found`

Make sure this file exists:

```text
database/.env
```

and contains:

```env
DATABASE_URL=YOUR_CONNECTION_STRING
```

Make sure the file is named exactly:

```text
.env
```

and not:

```text
.env.txt
```

---

## `Connection failed`

Check the following:

* Internet connection
* Neon database status
* PostgreSQL connection string
* Username
* Password
* Database name
* `.env` file location
* Whether the database is accessible

---

## `duplicate key value violates unique constraint`

This usually means that the database already contains the record or that the CSV contains a duplicate value in a field that must be unique.

If this happens:

1. Check whether the database has already been populated.
2. Check the CSV for duplicate values.
3. Do not immediately remove database constraints.
4. Check with the team before modifying existing database records.

---

## `relation does not exist`

This means that the required PostgreSQL table does not exist.

If setting up a new database:

1. Open `buildsync_schema.sql`.
2. Run the complete SQL script.
3. Verify that the 14 tables were created.
4. Run `python import_data.py`.

---

## Import Stops Partway Through

If the import stops during one of the tables:

1. Read the error message.
2. Identify the table where the error occurred.
3. Check the corresponding CSV.
4. Check the database constraint involved.
5. Do not repeatedly rerun the import against the same partially populated database without checking the problem first.

---

# Database Status

Current BuildSync dataset:

```text
14 tables
500 records per table
7,000 total records
```

Database:

```text
PostgreSQL
```

Shared hosted database:

```text
Neon PostgreSQL
```

Schema file:

```text
buildsync_schema.sql
```

Dataset folder:

```text
construction_resource_management_dataset/
```

Import script:

```text
import_data.py
```

Dataset generator:

```text
construction_resource_management_generator.py
```

---

# Project Team Notes

When working on the BuildSync database:

* Pull the latest repository changes before starting work.
* Do not commit `.env`.
* Do not expose database credentials.
* Keep database column names consistent with the PostgreSQL schema.
* Coordinate database schema changes with the team before modifying existing tables.
* Use the finalized CSV dataset for the current project.
* Do not run `import_data.py` on the shared Neon database unless the database needs to be initialized again.
* Keep `buildsync_schema.sql` updated if the database structure is intentionally changed.
* Keep the generator script available for future dataset generation.
* Do not delete the finalized CSV dataset from the repository.

---

# Quick Start for Team Members

If the shared Neon database is already populated, follow these steps:

## 1. Clone the Repository

```powershell
git clone YOUR_REPOSITORY_URL
```

## 2. Enter the Project

```powershell
cd WebSys-G3
```

## 3. Create a Virtual Environment

```powershell
py -m venv .venv
```

## 4. Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 5. Install the Database Packages

```powershell
python -m pip install "psycopg[binary]" python-dotenv
```

## 6. Create `.env`

Inside:

```text
database/.env
```

add:

```env
DATABASE_URL=YOUR_NEON_CONNECTION_STRING
```

## 7. Do Not Import the Dataset Again

The shared Neon database is already populated.

Do **not** run:

```powershell
python import_data.py
```

unless you are initializing a new or empty database.

## 8. Run the BuildSync Application

Start the backend and frontend according to the project's main setup instructions.

The backend should use the `DATABASE_URL` from:

```text
database/.env
```

to connect to the shared Neon PostgreSQL database.

---

# For a New or Empty Database

If you are setting up a completely new PostgreSQL database:

```text
1. Create the PostgreSQL/Neon database
        ↓
2. Open buildsync_schema.sql
        ↓
3. Run the SQL schema
        ↓
4. Verify the 14 tables
        ↓
5. Create database/.env
        ↓
6. Add DATABASE_URL
        ↓
7. Install Python packages
        ↓
8. Run import_data.py
        ↓
9. Verify the 7,000 records
        ↓
10. Connect the backend
```

Use:

```powershell
python import_data.py
```

only for this type of setup.

---

# BuildSync

**Construction Management Resource System**

Database: PostgreSQL
Hosted Database: Neon PostgreSQL
Dataset: Construction Resource Management Dataset

```

Available next action: :contentReference[oaicite:0]{index=0}
```
