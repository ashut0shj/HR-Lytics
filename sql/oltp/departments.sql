-- get all departments
SELECT * FROM departments ORDER BY department_name;

-- find a department by name
SELECT department_id FROM departments WHERE department_name = %(n)s;

-- insert a new department
INSERT INTO departments (department_name) VALUES (%(n)s);

