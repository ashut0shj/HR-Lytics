from src.db.db_wrapper import DBWrapper
from src.models.models import Employee, Department, Project

db = DBWrapper()

data = db.fetch_one("SELECT * FROM employees WHERE employee_id = %s", (1,))
if data:
    emp = Employee(**data)
    print("Employee loaded:", emp.full_name, "Salary:", emp.salary)
    emp.give_raise(5)
    db.execute_query("UPDATE employees SET salary = %s WHERE employee_id = %s", (emp.salary, emp.employee_id))
    print("Updated salary:", emp.salary)

rows = db.fetch_all("SELECT * FROM employees LIMIT 3")
for item in rows:
    e = Employee(**item)
    print("Row:", e.full_name, e.salary)

dept_data = db.fetch_one("SELECT * FROM departments LIMIT 1")
if dept_data:
    dept = Department(**dept_data)
    print("Department:", dept.department_name, dept.location)

db.close()