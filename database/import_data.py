import os
import csv
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()
if not os.getenv("DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parent / ".env")
if not os.getenv("DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
if not os.getenv("DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found. "
        "Check your .env file."
    )


# ==========================================
# DATASET LOCATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = (
    BASE_DIR / "construction_resource_management_dataset"
)


# ==========================================
# IMPORT ORDER
# ==========================================

FILES = [
    ("historical_material_demand", "historical_material_demand.csv"),
]


# ==========================================
# HELPER FUNCTION
# ==========================================

def clean_value(value):
    """
    Convert empty CSV values into PostgreSQL NULL.
    """
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    return value


# ==========================================
# IMPORT FUNCTION
# ==========================================

def import_csv(cursor, table_name, filename):

    file_path = DATASET_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    print(f"\nImporting {filename} -> {table_name}")

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(
                f"No headers found in {filename}"
            )

        columns = reader.fieldnames

        # PostgreSQL column names
        column_sql = ", ".join(
            f'"{column}"'
            for column in columns
        )

        placeholders = ", ".join(
            ["%s"] * len(columns)
        )

        query = f"""
            INSERT INTO "{table_name}"
            ({column_sql})
            VALUES ({placeholders})
        """

        rows = []

        for row in reader:

            values = [
                clean_value(row[column])
                for column in columns
            ]

            rows.append(values)

        cursor.executemany(query, rows)

        print(
            f"   ✓ Inserted {len(rows)} records"
        )


# ==========================================
# MAIN
# ==========================================

def main():

    print("=" * 50)
    print("BUILDSYNC DATA IMPORT")
    print("=" * 50)

    print("\nConnecting to Neon...")

    with psycopg.connect(DATABASE_URL) as connection:

        print("✓ Connected to Neon!")

        with connection.cursor() as cursor:

            for table_name, filename in FILES:

                import_csv(
                    cursor,
                    table_name,
                    filename
                )

        # Commit everything
        connection.commit()

    print("\n" + "=" * 50)
    print("IMPORT COMPLETE!")
    print("=" * 50)

    print("\nImported:")
    print("15 tables")
    print("14 original tables + 1 historical demand table")
    print("8,200 total records")

    print("\nYour BuildSync database is now populated.")


if __name__ == "__main__":
    main()