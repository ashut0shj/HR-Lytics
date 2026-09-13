from src.db.db_wrapper import DBWrapper

db = DBWrapper()


tables = db.fetch_all("SHOW TABLES")
print(tables)
print("Tables count:", len(tables))

employees = db.fetch_all("SELECT employee_id, first_name, salary FROM employees LIMIT 3")
print(employees)
for item in employees:
    print("Employee:", item)

emp = db.fetch_one("SELECT * FROM employees WHERE employee_id = %s", (1,))
print("Single employee:", emp)

db.execute_query("UPDATE employees SET salary = salary WHERE employee_id = %s", (1,))
print("Update executed successfully")

db.close()