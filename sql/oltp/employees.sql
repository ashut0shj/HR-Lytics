-- insert a new employee
INSERT INTO employees
    (employee_id, first_name, last_name, email, gender, age,
     department_id, job_role, job_level, monthly_income,
     hire_date, attrition)
VALUES
    (%(employee_id)s, %(first_name)s, %(last_name)s, %(email)s, %(gender)s, %(age)s,
     %(department_id)s, %(job_role)s, %(job_level)s, %(monthly_income)s,
     %(hire_date)s, %(attrition)s);

-- get all employees sorted by newest first
SELECT * FROM employees ORDER BY employee_id DESC LIMIT %(limit)s;

-- get a single employee by id
SELECT * FROM employees WHERE employee_id = %(id)s;

-- update employee's department
UPDATE employees SET department_id = %(dept_id)s WHERE employee_id = %(emp_id)s;

-- delete an employee
DELETE FROM employees WHERE employee_id = %(id)s;

-- get max employee id for next id generation
SELECT MAX(employee_id) AS max_id FROM employees;

