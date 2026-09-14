-- insert a new project
INSERT INTO projects (project_name, department_id, start_date, end_date)
VALUES (%(name)s, %(dept_id)s, %(start)s, %(end)s);

-- get all projects newest first
SELECT * FROM projects ORDER BY project_id DESC;

-- assign an employee to a project
INSERT INTO assignments (employee_id, project_id, role_on_project, assigned_date)
VALUES (%(emp)s, %(proj)s, %(role)s, %(today)s);

