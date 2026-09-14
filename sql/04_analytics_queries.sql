-- =====================================================================
-- 04_analytics_queries.sql
-- These are the "advanced SQL" queries the Streamlit dashboard runs
-- against the OLAP warehouse. They demonstrate CTEs (Common Table
-- Expressions — a WITH block that names a temporary result set) and
-- WINDOW FUNCTIONS (calculations across a set of rows related to the
-- current row, without collapsing them into one row like GROUP BY does).
-- =====================================================================
-- Reference analytics queries demonstrating CTEs and window functions.
-- These run against the hr_olap data warehouse and are the basis for
-- the charts and tables in the Streamlit dashboard.

USE hr_olap;

-- ---------------------------------------------------------------------
-- 1. Top-performing employees PER DEPARTMENT using DENSE_RANK()
--    Beginner note: DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)
--    restarts the ranking for every department (the "partition") and
--    gives tied scores the same rank without skipping numbers.
-- ---------------------------------------------------------------------
-- 1. Top performers per department using DENSE_RANK()
--    DENSE_RANK() restarts numbering for each department partition and
--    doesn't skip ranks when scores are tied (unlike RANK()).
WITH ranked_employees AS (
    SELECT
        de.department_name,
        de.first_name,
        de.last_name,
        f.performance_rating,
        DENSE_RANK() OVER (
            PARTITION BY de.department_name
            ORDER BY f.performance_rating DESC
        ) AS performance_rank
    FROM Fact_PerformanceReviews f
    JOIN Dim_Employee de ON de.employee_key = f.employee_key
)
SELECT department_name, first_name, last_name, performance_rating, performance_rank
FROM ranked_employees
WHERE performance_rank <= 3
ORDER BY department_name, performance_rank;


-- ---------------------------------------------------------------------
-- 2. Year-over-year average performance trend
-- ---------------------------------------------------------------------
SELECT
    dd.year,
    ROUND(AVG(f.performance_rating), 2) AS avg_performance,
    ROUND(AVG(f.job_satisfaction), 2)   AS avg_job_satisfaction,
    COUNT(*) AS review_count
FROM Fact_PerformanceReviews f
JOIN Dim_Date dd ON dd.date_key = f.date_key
GROUP BY dd.year
ORDER BY dd.year;


-- ---------------------------------------------------------------------
-- 3. Attrition risk score using a CTE + window function
--    We flag employees whose income sits in the bottom 25% of their
--    department (NTILE splits each department's employees into 4 equal
--    buckets) AND whose satisfaction is low, as "higher attrition risk".
-- ---------------------------------------------------------------------
-- 3. Attrition risk scoring with CTE + NTILE window function
--    NTILE(4) divides employees within each department into four equal income
--    buckets. Bottom-quartile earners with low satisfaction are flagged High Risk.
WITH income_buckets AS (
    SELECT
        de.employee_id,
        de.first_name,
        de.last_name,
        de.department_name,
        de.monthly_income,
        f.job_satisfaction,
        f.work_life_balance,
        NTILE(4) OVER (
            PARTITION BY de.department_name
            ORDER BY de.monthly_income
        ) AS income_quartile
    FROM Dim_Employee de
    JOIN Fact_PerformanceReviews f ON f.employee_key = de.employee_key
    WHERE de.is_current = 1
)
SELECT
    employee_id, first_name, last_name, department_name,
    monthly_income, job_satisfaction, work_life_balance,
    CASE
        WHEN income_quartile = 1 AND job_satisfaction <= 2 THEN 'High Risk'
        WHEN income_quartile = 1 OR job_satisfaction <= 2 THEN 'Medium Risk'
        WHEN income_quartile = 1 OR  job_satisfaction <= 2 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS attrition_risk
FROM income_buckets
ORDER BY FIELD(attrition_risk, 'High Risk', 'Medium Risk', 'Low Risk');


-- ---------------------------------------------------------------------
-- 4. Department headcount + running total (window function SUM() OVER)
-- ---------------------------------------------------------------------
-- 4. Department headcount with running total (SUM() OVER)
WITH dept_counts AS (
    SELECT department_name, COUNT(*) AS headcount
    FROM Dim_Employee
    WHERE is_current = 1
    GROUP BY department_name
)
SELECT
    department_name,
    headcount,
    SUM(headcount) OVER (ORDER BY headcount DESC) AS running_total_headcount
FROM dept_counts
ORDER BY headcount DESC;


-- ---------------------------------------------------------------------
-- 5. Employees who changed department (uses the SCD2 history directly)
-- ---------------------------------------------------------------------
-- 5. Employees who changed department — uses SCD2 history directly
SELECT
    old.employee_id,
    old.first_name,
    old.last_name,
    old.department_name AS old_department,
    new.department_name AS new_department,
    old.end_date AS changed_on
    old.end_date        AS changed_on
FROM Dim_Employee old
JOIN Dim_Employee new
    ON new.employee_id = old.employee_id
   AND new.is_current = 1
    ON  new.employee_id = old.employee_id
    AND new.is_current  = 1
WHERE old.is_current = 0
  AND old.department_name <> new.department_name;
