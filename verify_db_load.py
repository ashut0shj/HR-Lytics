import os
from src.db.db_wrapper import DBWrapper

def verify_db_load():
    print("Connecting to database to verify data load...")
    db = DBWrapper()
    
    queries = {
        "OLTP - Staging Employees": "SELECT COUNT(*) as count FROM staging_employees",
        "OLTP - Staging History": "SELECT COUNT(*) as count FROM staging_employee_history",
        "OLTP - Employees": "SELECT COUNT(*) as count FROM employees",
        "OLAP - Dim_Employee": "SELECT COUNT(*) as count FROM hr_olap.Dim_Employee",
        "OLAP - Fact_PerformanceReviews": "SELECT COUNT(*) as count FROM hr_olap.Fact_PerformanceReviews"
    }

    all_good = True
    print("\n--- DATABASE ROW COUNTS ---")
    for name, query in queries.items():
        try:
            result = db.fetch_one(query)
            count = result['count'] if result else 0
            print(f"{name}: {count} rows")
            if count == 0:
                all_good = False
        except Exception as e:
            print(f"{name}: ERROR - {e}")
            all_good = False

    print("---------------------------\n")
    if all_good:
        print("✅ SUCCESS: Data is loaded into both OLTP and OLAP databases!")
    else:
        print("❌ WARNING: Some tables are empty. The dataset has not been fully loaded yet.")

if __name__ == "__main__":
    # Ensure working directory is project root
    if not os.path.exists('.env'):
        os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    verify_db_load()

