-- headcount per department (current employees only)
SELECT department_name, COUNT(*) AS headcount
FROM Dim_Employee
WHERE is_current = 1
GROUP BY department_name
ORDER BY headcount DESC;

-- attrition breakdown with average income
SELECT attrition, COUNT(*) AS employee_count, AVG(monthly_income) AS avg_income
FROM Dim_Employee
WHERE is_current = 1
GROUP BY attrition;

-- average salary per job role
SELECT job_role, AVG(monthly_income) AS avg_income, COUNT(*) AS n
FROM Dim_Employee
WHERE is_current = 1
GROUP BY job_role
ORDER BY avg_income DESC;

-- year over year avg performance and satisfaction trend
SELECT dd.year,
       AVG(f.performance_rating) AS avg_performance,
       AVG(f.job_satisfaction) AS avg_job_satisfaction,
       COUNT(*) AS review_count
FROM Fact_PerformanceReviews f
JOIN Dim_Date dd ON dd.date_key = f.date_key
GROUP BY dd.year
ORDER BY dd.year;

-- top performers ranked per department using window function
WITH ranked AS (
    SELECT
        de.department_name, de.first_name, de.last_name,
        f.performance_rating,
        RANK() OVER (
            PARTITION BY de.department_name
            ORDER BY f.performance_rating DESC
        ) AS perf_rank
    FROM Fact_PerformanceReviews f
    JOIN Dim_Employee de ON de.employee_key = f.employee_key
)
SELECT * FROM ranked WHERE perf_rank <= {top_n}
ORDER BY department_name, perf_rank;

-- employees who changed departments (scd2 history rows)
SELECT old.employee_id, old.first_name, old.last_name,
       old.department_name AS old_department,
       new.department_name AS new_department,
       old.end_date AS changed_on
FROM Dim_Employee old
JOIN Dim_Employee new ON new.employee_id = old.employee_id AND new.is_current = 1
WHERE old.is_current = 0
ORDER BY old.end_date DESC
LIMIT {limit};

-- close the current dim_employee row before inserting a new one
UPDATE Dim_Employee
SET is_current = 0, end_date = %(yesterday)s
WHERE employee_id = %(emp_id)s AND is_current = 1;

-- fetch old dim_employee row to carry attributes forward
SELECT first_name, last_name, gender, age, job_role,
       job_level, monthly_income, attrition
FROM Dim_Employee
WHERE employee_id = %(emp_id)s
ORDER BY employee_key DESC LIMIT 1;

-- insert updated current row for scd2 department change
INSERT INTO Dim_Employee
    (employee_id, first_name, last_name, gender, age,
     department_name, job_role, job_level, monthly_income,
     attrition, start_date, end_date, is_current)
VALUES
    (%(emp_id)s, %(fn)s, %(ln)s, %(gender)s, %(age)s, %(dept)s, %(role)s,
     %(level)s, %(income)s, %(attr)s, %(start)s, NULL, 1);

