import os
import pandas as pd
from src.db.db_wrapper import DBWrapper

def load_csv_to_staging():
    print("Connecting to database...")
    db = DBWrapper()
    
    current_csv = os.path.join("dataset", "staging_employees.csv")
    history_csv = os.path.join("dataset", "staging_employee_history.csv")
    
    if not os.path.exists(current_csv):
        print(f"Error: {current_csv} not found. Run generate_data.py first.")
        return

    print(f"Loading {current_csv} into staging_employees...")
    df_current = pd.read_csv(current_csv)
    # Replace NaNs with None for SQL
    df_current = df_current.where(pd.notnull(df_current), None)
    
    # Columns defined in our staging_employees SQL table
    staging_emp_cols = [
        "employee_id", "Age", "Attrition", "Department", "DistanceFromHome",
        "Education", "EducationField", "Gender", "JobLevel", "JobRole",
        "JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction",
        "WorkLifeBalance", "MonthlyIncome", "PerformanceRating",
        "first_name", "last_name", "email", "hire_date",
        "scd_start_date", "scd_end_date", "is_current"
    ]
    # Filter the CSV dataframe to ONLY these columns
    df_current = df_current[[col for col in staging_emp_cols if col in df_current.columns]]
    
    # We need to construct an INSERT query matching the columns
    cols = list(df_current.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    sql_current = f"INSERT INTO staging_employees ({', '.join(cols)}) VALUES ({placeholders})"
    
    # execute_many handles batches but converting to list of tuples is needed
    data_current = [tuple(row) for row in df_current.to_numpy()]
    
    # Chunk the inserts so we don't blow up memory/packet size
    chunk_size = 5000
    for i in range(0, len(data_current), chunk_size):
        chunk = data_current[i:i+chunk_size]
        success = db.execute_many(sql_current, chunk)
        if not success:
            print(f"Failed loading chunk {i} to {i+chunk_size} into staging_employees.")
            return
        print(f"Loaded {min(i+chunk_size, len(data_current))} / {len(data_current)} rows...")
    
    if os.path.exists(history_csv):
        print(f"Loading {history_csv} into staging_employee_history...")
        df_history = pd.read_csv(history_csv)
        df_history = df_history.where(pd.notnull(df_history), None)
        
        hist_cols = [
            "employee_id", "Department", "JobRole", "JobLevel",
            "MonthlyIncome", "scd_start_date", "scd_end_date", "is_current"
        ]
        df_history = df_history[[col for col in hist_cols if col in df_history.columns]]
        
        cols_hist = list(df_history.columns)
        placeholders_hist = ", ".join(["%s"] * len(cols_hist))
        sql_history = f"INSERT INTO staging_employee_history ({', '.join(cols_hist)}) VALUES ({placeholders_hist})"
        
        data_history = [tuple(row) for row in df_history.to_numpy()]
        for i in range(0, len(data_history), chunk_size):
            chunk = data_history[i:i+chunk_size]
            success = db.execute_many(sql_history, chunk)
            if not success:
                print(f"Failed loading chunk {i} to {i+chunk_size} into staging_employee_history.")
                return
            print(f"Loaded {min(i+chunk_size, len(data_history))} / {len(data_history)} rows...")

    print("Executing ETL procedures to move data to OLAP...")
    
    # Run the ETL procedures
    # Note: DBWrapper connects to hr_oltp by default (from .env), but the procedures are in hr_olap
    # However, our procedures explicitly say USE hr_olap inside them if run via CLI, 
    # but via python we might need to specify the schema if it's cross-database.
    # The procedures cross-reference hr_oltp. We can just run them if they exist in hr_olap.
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("Calling sp_load_dim_date...")
        cursor.execute("CALL hr_olap.sp_load_dim_date('2015-01-01', '2027-12-31')")
        
        print("Calling sp_load_dim_department...")
        cursor.execute("CALL hr_olap.sp_load_dim_department()")
        
        print("Calling sp_load_dim_project...")
        cursor.execute("CALL hr_olap.sp_load_dim_project()")
        
        print("Calling sp_load_dim_employee_scd2...")
        cursor.execute("CALL hr_olap.sp_load_dim_employee_scd2()")
        
        print("Calling sp_load_fact_performance_reviews...")
        cursor.execute("CALL hr_olap.sp_load_fact_performance_reviews()")
        
        conn.commit()
        cursor.close()
        print("ETL completed successfully!")
    except Exception as e:
        print(f"ETL Execution failed: {e}")

    print("Migration finished!")

if __name__ == "__main__":
    # Ensure working directory is project root
    if not os.path.exists('dataset'):
        os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    load_csv_to_staging()

