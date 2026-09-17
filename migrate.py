"""
migrate.py — Full one-shot migration from CSVs into both OLTP and OLAP databases.

Run this from the project root:
    python migrate.py
"""

import os
import sys
import subprocess
import pandas as pd
from src.db_wrapper import DBWrapper

CHUNK_SIZE = 5000

SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")

CURRENT_CSV = os.path.join(DATASET_DIR, "staging_employees.csv")
HISTORY_CSV = os.path.join(DATASET_DIR, "staging_employee_history.csv")


def get_connection(database=""):
    """Get a raw connection via DBWrapper (defaulting to no database / server root)."""
    db = DBWrapper(database=database)
    return db.get_connection()


def run_sql_file(filepath):
    """Execute a .sql file against the server root."""
    print(f"  Running {os.path.basename(filepath)}...")
    with open(filepath, "r") as f:
        sql = f.read()

    db = DBWrapper(database="")
    conn = db.get_connection()
    cursor = conn.cursor()

    def exec_stmt(stmt):
        stmt = stmt.strip()
        if not stmt:
            return
        try:
            cursor.execute(stmt)
        except Exception as e:
            if "Duplicate key name" in str(e):
                return
            cursor.close()
            db.close()
            sys.exit(
                f"\n  SQL error while running {os.path.basename(filepath)}:\n"
                f"  {e}\n\n"
                f"  Failing statement:\n  {stmt[:200]}\n\n"
                f"  Stopping here so later steps don't run against a half-built database."
            )

    if "DELIMITER $$" in sql or "DELIMITER\t$$" in sql:
        pre, rest = sql.split("DELIMITER $$", 1)
        for stmt in pre.split(";"):
            exec_stmt(stmt)

        proc_section = rest.split("DELIMITER ;")[0]
        for block in proc_section.split("$$"):
            exec_stmt(block)
    else:
        for stmt in sql.split(";"):
            exec_stmt(stmt)

    conn.commit()
    cursor.close()
    db.close()


def truncate_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = [
        "hr_oltp.staging_employees",
        "hr_oltp.staging_employee_history",
        "hr_oltp.employees",
        "hr_oltp.departments",
        "hr_oltp.projects",
        "hr_oltp.assignments",
        "hr_oltp.reviews",
        "hr_olap.Dim_Employee",
        "hr_olap.Dim_Department",
        "hr_olap.Dim_Project",
        "hr_olap.Dim_Date",
        "hr_olap.Fact_PerformanceReviews",
    ]
    for tbl in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {tbl};")
        except Exception:
            pass
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    cursor.close()


def bulk_insert(conn, table, df, chunk_size=CHUNK_SIZE):
    """Insert a DataFrame into a MySQL table in chunks using INSERT IGNORE."""
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"INSERT IGNORE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    data = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]
    cursor = conn.cursor()
    total = len(data)
    for i in range(0, total, chunk_size):
        chunk = data[i : i + chunk_size]
        cursor.executemany(sql, chunk)
        conn.commit()
        print(f"    {min(i + chunk_size, total):>7,} / {total:,}")
    cursor.close()


def verify(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def step_generate_data():
    if os.path.exists(CURRENT_CSV) and os.path.exists(HISTORY_CSV):
        print("  CSVs already exist — skipping generation.")
        return
    print("  Running generate_data.py...")
    result = subprocess.run(
        [sys.executable, "-m", "src.generate_data"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr)
        sys.exit("Data generation failed. Aborting.")
    print("  Done.")


def step_init_schemas():
    run_sql_file(os.path.join(SQL_DIR, "01_oltp_schema.sql"))
    run_sql_file(os.path.join(SQL_DIR, "02_olap_schema.sql"))
    run_sql_file(os.path.join(SQL_DIR, "03_etl_procedures.sql"))
    print("  Schemas and procedures initialized.")


def step_load_staging(conn):
    print(f"  Reading {os.path.basename(CURRENT_CSV)}...")
    df = pd.read_csv(CURRENT_CSV, low_memory=False)
    df = df.where(pd.notnull(df), None)

    staging_cols = [
        "employee_id", "Age", "Attrition", "BusinessTravel", "DailyRate",
        "Department", "DistanceFromHome", "Education", "EducationField",
        "EmployeeCount", "EmployeeNumber", "EnvironmentSatisfaction", "Gender",
        "HourlyRate", "JobInvolvement", "JobLevel", "JobRole", "JobSatisfaction",
        "MaritalStatus", "MonthlyIncome", "MonthlyRate", "NumCompaniesWorked",
        "Over18", "OverTime", "PercentSalaryHike", "PerformanceRating",
        "RelationshipSatisfaction", "StandardHours", "StockOptionLevel",
        "TotalWorkingYears", "TrainingTimesLastYear", "WorkLifeBalance",
        "YearsAtCompany", "YearsInCurrentRole", "YearsSinceLastPromotion",
        "YearsWithCurrManager", "first_name", "last_name", "email",
        "hire_date", "scd_start_date", "scd_end_date", "is_current",
    ]
    df = df[[c for c in staging_cols if c in df.columns]]
    print(f"  Inserting {len(df):,} rows into staging_employees...")
    bulk_insert(conn, "staging_employees", df)

    if not os.path.exists(HISTORY_CSV):
        print("  No history CSV found, skipping.")
        return

    print(f"  Reading {os.path.basename(HISTORY_CSV)}...")
    dh = pd.read_csv(HISTORY_CSV, low_memory=False)
    dh = dh.where(pd.notnull(dh), None)

    hist_cols = [
        "employee_id", "Department", "JobRole", "JobLevel",
        "MonthlyIncome", "scd_start_date", "scd_end_date", "is_current",
    ]
    dh = dh[[c for c in hist_cols if c in dh.columns]]
    print(f"  Inserting {len(dh):,} rows into staging_employee_history...")
    bulk_insert(conn, "staging_employee_history", dh)


def step_populate_departments(conn):
    sql = """
        INSERT IGNORE INTO departments (department_name)
        SELECT DISTINCT Department
        FROM staging_employees
        WHERE Department IS NOT NULL
        ORDER BY Department
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    count = cursor.rowcount
    cursor.close()
    print(f"  Inserted {count} departments into hr_oltp.departments.")


def step_populate_employees(conn):
    sql = """
        INSERT IGNORE INTO employees (
            employee_id, first_name, last_name, email, gender, age,
            department_id, job_role, job_level, monthly_income, hire_date,
            attrition, employee_number, business_travel, daily_rate,
            distance_from_home, education, education_field, employee_count,
            hourly_rate, marital_status, monthly_rate, num_companies_worked,
            over_18, over_time, percent_salary_hike, standard_hours,
            stock_option_level, total_working_years, years_at_company,
            years_in_current_role, years_since_last_promotion, years_with_curr_manager
        )
        SELECT
            s.employee_id, s.first_name, s.last_name, s.email, s.Gender, s.Age,
            d.department_id, s.JobRole, s.JobLevel, s.MonthlyIncome, s.hire_date,
            s.Attrition, s.EmployeeNumber, s.BusinessTravel, s.DailyRate,
            s.DistanceFromHome, s.Education, s.EducationField, s.EmployeeCount,
            s.HourlyRate, s.MaritalStatus, s.MonthlyRate, s.NumCompaniesWorked,
            s.Over18, s.OverTime, s.PercentSalaryHike, s.StandardHours,
            s.StockOptionLevel, s.TotalWorkingYears, s.YearsAtCompany,
            s.YearsInCurrentRole, s.YearsSinceLastPromotion, s.YearsWithCurrManager
        FROM staging_employees s
        LEFT JOIN departments d ON d.department_name = s.Department
        WHERE s.is_current = 1
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    count = cursor.rowcount
    cursor.close()
    print(f"  Inserted {count:,} employees into hr_oltp.employees.")


def step_run_etl(conn):
    procedures = [
        ("sp_load_dim_date",                "hr_olap.sp_load_dim_date('2018-01-01', '2027-12-31')"),
        ("sp_load_dim_department",          "hr_olap.sp_load_dim_department()"),
        ("sp_load_dim_project",             "hr_olap.sp_load_dim_project()"),
        ("sp_load_dim_employee_scd2",       "hr_olap.sp_load_dim_employee_scd2()"),
        ("sp_load_dim_employee_incremental","hr_olap.sp_load_dim_employee_incremental()"),
        ("sp_load_fact_performance_reviews","hr_olap.sp_load_fact_performance_reviews()"),
        ("sp_load_fact_reviews_incremental","hr_olap.sp_load_fact_reviews_incremental()"),
    ]
    cursor = conn.cursor()
    for name, call in procedures:
        print(f"  CALL {name}...")
        try:
            cursor.execute(f"CALL {call}")
            while cursor.nextset():
                pass
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name} FAILED")
            print(f"  Error: {e}")
            raise
    conn.commit()
    cursor.close()


def step_verify():
    tables = {
        "hr_oltp": [
            "departments", "employees", "staging_employees", "staging_employee_history",
        ],
        "hr_olap": [
            "Dim_Employee", "Dim_Department", "Dim_Date", "Fact_PerformanceReviews",
        ],
    }

    print()
    print("=" * 52)
    print("  MIGRATION SUMMARY")
    print("=" * 52)
    all_ok = True
    for db_name, table_list in tables.items():
        db = DBWrapper(database=db_name)
        conn = db.get_connection()
        for table in table_list:
            count = verify(conn, table)
            status = "✅" if count > 0 else "❌ EMPTY"
            if count == 0:
                all_ok = False
            print(f"  {status}  {db_name}.{table:<35} {count:>10,} rows")
        db.close()
    print("=" * 52)
    if all_ok:
        print("  All tables populated successfully.")
    else:
        print("  Some tables are still empty — check errors above.")
    print()


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print()
    print("HR-Lytics — Full Database Migration")
    print("=" * 52)

    print("\n[1/6] Generating synthetic dataset...")
    step_generate_data()

    print("\n[2/6] Initializing schemas and stored procedures...")
    step_init_schemas()

    print("\n[3/6] Resetting and loading staging CSVs into hr_oltp...")
    db_oltp = DBWrapper(database="hr_oltp")
    conn_oltp = db_oltp.get_connection()
    truncate_tables(conn_oltp)
    step_load_staging(conn_oltp)

    print("\n[4/6] Populating hr_oltp.departments...")
    step_populate_departments(conn_oltp)

    print("\n[5/6] Populating hr_oltp.employees from staging...")
    step_populate_employees(conn_oltp)
    db_oltp.close()

    print("\n[6/6] Running OLAP ETL procedures...")
    db_olap = DBWrapper(database="hr_olap")
    conn_olap = db_olap.get_connection()
    step_run_etl(conn_olap)
    db_olap.close()

    print("\nVerifying row counts...")
    step_verify()