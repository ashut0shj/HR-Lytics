-- headcount per department (current employees only)
SELECT department_name, COUNT(*) AS headcount
FROM hr_olap.Dim_Employee
WHERE is_current = 1
GROUP BY department_name
ORDER BY headcount DESC;

-- attrition breakdown with average income
SELECT attrition, COUNT(*) AS employee_count, AVG(monthly_income) AS avg_income
FROM hr_olap.Dim_Employee
WHERE is_current = 1
GROUP BY attrition;

-- average salary per job role
SELECT job_role, AVG(monthly_income) AS avg_income, COUNT(*) AS n
FROM hr_olap.Dim_Employee
WHERE is_current = 1
GROUP BY job_role
ORDER BY avg_income DESC;

-- year over year avg performance and satisfaction trend
SELECT dd.year,
       AVG(f.performance_rating) AS avg_performance,
       AVG(f.job_satisfaction) AS avg_job_satisfaction,
       COUNT(*) AS review_count
FROM hr_olap.Fact_PerformanceReviews f
JOIN hr_olap.Dim_Date dd ON dd.date_key = f.date_key
GROUP BY dd.year
ORDER BY dd.year;

-- top performers ranked per department using window function
WITH emp_scores AS (
    SELECT
        de.department_name, de.first_name, de.last_name, de.employee_id,
        AVG(f.performance_rating) AS avg_performance_rating
    FROM hr_olap.Fact_PerformanceReviews f
    JOIN hr_olap.Dim_Employee de ON de.employee_key = f.employee_key
    WHERE de.is_current = 1
    GROUP BY de.employee_key, de.department_name, de.first_name, de.last_name, de.employee_id
),
ranked AS (
    SELECT
        department_name, first_name, last_name, employee_id,
        avg_performance_rating AS performance_rating,
        ROW_NUMBER() OVER (
            PARTITION BY department_name
            ORDER BY avg_performance_rating DESC, employee_id ASC
        ) AS perf_rank
    FROM emp_scores
)
SELECT * FROM ranked WHERE perf_rank <= {top_n}
ORDER BY department_name, perf_rank;

-- employees who changed departments (scd2 history rows)
SELECT old.employee_id, old.first_name, old.last_name,
       old.department_name AS old_department,
       new.department_name AS new_department,
       old.end_date AS changed_on
FROM hr_olap.Dim_Employee old
JOIN hr_olap.Dim_Employee new ON new.employee_id = old.employee_id AND new.is_current = 1
WHERE old.is_current = 0
ORDER BY old.end_date DESC
LIMIT {limit};

-- close the current dim_employee row before inserting a new one
UPDATE hr_olap.Dim_Employee
SET is_current = 0, end_date = %(yesterday)s
WHERE employee_id = %(emp_id)s AND is_current = 1;

-- fetch old dim_employee row to carry attributes forward
SELECT first_name, last_name, gender, age, job_role,
       job_level, monthly_income, attrition
FROM hr_olap.Dim_Employee
WHERE employee_id = %(emp_id)s
ORDER BY employee_key DESC LIMIT 1;

-- insert updated current row for scd2 department change
INSERT INTO hr_olap.Dim_Employee
    (employee_id, first_name, last_name, gender, age,
     department_name, job_role, job_level, monthly_income,
     attrition, start_date, end_date, is_current)
VALUES
    (%(emp_id)s, %(fn)s, %(ln)s, %(gender)s, %(age)s, %(dept)s, %(role)s,
     %(level)s, %(income)s, %(attr)s, %(start)s, NULL, 1);

-- attrition risk by satisfaction and department benchmarks
WITH latest_reviews AS (
    SELECT
        f.employee_key,
        f.performance_rating,
        f.job_satisfaction,
        f.environment_satisfaction,
        f.relationship_satisfaction,
        f.work_life_balance,
        ROW_NUMBER() OVER (
            PARTITION BY f.employee_key
            ORDER BY f.date_key DESC, f.review_key DESC
        ) AS rn
    FROM hr_olap.Fact_PerformanceReviews f
),
emp_benchmarks AS (
    SELECT
        de.employee_id,
        de.first_name,
        de.last_name,
        de.department_name,
        de.job_role,
        de.job_level,
        de.monthly_income,
        lr.job_satisfaction,
        lr.work_life_balance,
        lr.environment_satisfaction,
        lr.relationship_satisfaction,
        lr.performance_rating,
        ROUND(AVG(lr.job_satisfaction) OVER (PARTITION BY de.department_name), 2) AS dept_avg_satisfaction,
        ROUND(AVG(lr.work_life_balance) OVER (PARTITION BY de.department_name), 2) AS dept_avg_wlb,
        ROUND(AVG(de.monthly_income) OVER (PARTITION BY de.department_name), 2) AS dept_avg_income,
        NTILE(4) OVER (PARTITION BY de.department_name ORDER BY de.monthly_income ASC) AS income_quartile
    FROM hr_olap.Dim_Employee de
    JOIN latest_reviews lr
        ON lr.employee_key = de.employee_key
       AND lr.rn = 1
    WHERE de.is_current = 1
      AND de.attrition = 'No'
),
risk_scoring AS (
    SELECT
        employee_id,
        first_name,
        last_name,
        department_name,
        job_role,
        job_level,
        monthly_income,
        dept_avg_income,
        income_quartile,
        job_satisfaction,
        dept_avg_satisfaction,
        work_life_balance,
        dept_avg_wlb,
        environment_satisfaction,
        relationship_satisfaction,
        performance_rating,
        (CASE WHEN job_satisfaction < dept_avg_satisfaction THEN 1 ELSE 0 END) AS flag_low_satisfaction,
        (CASE WHEN monthly_income < dept_avg_income THEN 1 ELSE 0 END) AS flag_low_income,
        (CASE WHEN work_life_balance < dept_avg_wlb OR work_life_balance <= 2 THEN 1 ELSE 0 END) AS flag_low_wlb,
        (CASE WHEN environment_satisfaction <= 2 THEN 1 ELSE 0 END) AS flag_low_env,
        (CASE WHEN relationship_satisfaction <= 2 THEN 1 ELSE 0 END) AS flag_low_rel
    FROM emp_benchmarks
),
risk_weighted AS (
    SELECT
        *,
        (flag_low_satisfaction * 3 +
         flag_low_income * 2 +
         flag_low_wlb * 2 +
         flag_low_env * 1 +
         flag_low_rel * 1) AS risk_points
    FROM risk_scoring
)
SELECT
    employee_id,
    CONCAT(first_name, ' ', last_name) AS employee_name,
    department_name,
    job_role,
    job_level,
    monthly_income,
    dept_avg_income,
    job_satisfaction,
    dept_avg_satisfaction,
    work_life_balance,
    environment_satisfaction,
    relationship_satisfaction,
    risk_points,
    CASE
        WHEN risk_points >= 6 THEN 'Critical Risk'
        WHEN risk_points >= 4 THEN 'High Risk'
        WHEN risk_points >= 2 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS attrition_risk_tier
FROM risk_weighted
ORDER BY risk_points DESC, job_satisfaction ASC;

