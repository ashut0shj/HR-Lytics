-- =====================================================================
-- 03_etl_procedures.sql
-- ETL = "Extract, Transform, Load". These stored procedures move data
-- OUT of the raw staging tables (loaded by the Python synthesizer) and
-- INTO the clean OLAP star schema (Dim_* and Fact_* tables).
--
-- Run this AFTER 02_olap_schema.sql. Because it reads from hr_oltp and
-- writes to hr_olap, both databases must exist on the same MySQL server.
-- =====================================================================

USE hr_olap;

DELIMITER $$

-- ---------------------------------------------------------------------
-- sp_load_dim_date
-- Beginner note: a date dimension is usually pre-built once, covering
-- a wide date range, so every fact row always finds a matching date_key.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_date $$
CREATE PROCEDURE sp_load_dim_date(IN start_date DATE, IN end_date DATE)
BEGIN
    DECLARE d DATE;
    SET d = start_date;

    WHILE d <= end_date DO
        INSERT IGNORE INTO Dim_Date (date_key, full_date, day, month, month_name, quarter, year)
        VALUES (
            CAST(DATE_FORMAT(d, '%Y%m%d') AS UNSIGNED),
            d,
            DAY(d),
            MONTH(d),
            MONTHNAME(d),
            QUARTER(d),
            YEAR(d)
        );
        SET d = DATE_ADD(d, INTERVAL 1 DAY);
    END WHILE;
END $$


-- ---------------------------------------------------------------------
-- sp_load_dim_department
-- Simple "insert what's missing" load — departments rarely change.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_department $$
CREATE PROCEDURE sp_load_dim_department()
BEGIN
    INSERT INTO Dim_Department (department_id, department_name)
    SELECT d.department_id, d.department_name
    FROM hr_oltp.departments d
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Department dd WHERE dd.department_id = d.department_id
    );
END $$


-- ---------------------------------------------------------------------
-- sp_load_dim_project
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_project $$
CREATE PROCEDURE sp_load_dim_project()
BEGIN
    INSERT INTO Dim_Project (project_id, project_name, department_name)
    SELECT p.project_id, p.project_name, dep.department_name
    FROM hr_oltp.projects p
    LEFT JOIN hr_oltp.departments dep ON dep.department_id = p.department_id
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Project dp WHERE dp.project_id = p.project_id
    );
END $$


-- ---------------------------------------------------------------------
-- sp_load_dim_employee_scd2
-- THE MAIN SCD TYPE 2 PROCEDURE.
--
-- Logic:
--   1. Load the "history" staging rows first (the OLD versions) as
--      closed-out (is_current = 0) dimension rows.
--   2. Load the "current" staging rows as open (is_current = 1) rows.
--   3. For any employee_id already in Dim_Employee whose attributes
--      changed compared to the incoming "current" row, close the old
--      dimension row and insert a fresh current one (this is what makes
--      it SCD2 rather than a one-time load — safe to re-run).
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_dim_employee_scd2 $$
CREATE PROCEDURE sp_load_dim_employee_scd2()
BEGIN
    -- Step 1: load historical (closed) versions from staging_employee_history
    INSERT INTO Dim_Employee (
        employee_id, first_name, last_name, gender, age,
        department_name, job_role, job_level, monthly_income, attrition,
        start_date, end_date, is_current
    )
    SELECT
        h.employee_id,
        e.first_name, e.last_name, e.Gender, e.Age,
        h.Department, h.JobRole, h.JobLevel, h.MonthlyIncome, e.Attrition,
        h.scd_start_date, h.scd_end_date, 0
    FROM hr_oltp.staging_employee_history h
    JOIN hr_oltp.staging_employees e ON e.employee_id = h.employee_id
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Employee de
        WHERE de.employee_id = h.employee_id AND de.is_current = 0
    );

    -- Step 2: close out any existing "current" row whose attributes
    -- differ from the new incoming current row (re-runnable SCD2 logic)
    UPDATE Dim_Employee de
    JOIN hr_oltp.staging_employees se ON se.employee_id = de.employee_id
    SET de.end_date = DATE_SUB(se.scd_start_date, INTERVAL 1 DAY),
        de.is_current = 0
    WHERE de.is_current = 1
      AND (
            de.department_name <> se.Department
         OR de.job_role        <> se.JobRole
         OR de.job_level       <> se.JobLevel
         OR de.monthly_income  <> se.MonthlyIncome
      );

    -- Step 3: insert the new current version for employees who either
    -- (a) never existed in Dim_Employee, or (b) were just closed in step 2
    INSERT INTO Dim_Employee (
        employee_id, first_name, last_name, gender, age,
        department_name, job_role, job_level, monthly_income, attrition,
        start_date, end_date, is_current
    )
    SELECT
        se.employee_id, se.first_name, se.last_name, se.Gender, se.Age,
        se.Department, se.JobRole, se.JobLevel, se.MonthlyIncome, se.Attrition,
        se.scd_start_date, NULL, 1
    FROM hr_oltp.staging_employees se
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Employee de
        WHERE de.employee_id = se.employee_id AND de.is_current = 1
    );
END $$


-- ---------------------------------------------------------------------
-- sp_load_fact_performance_reviews
-- Loads one fact row per staged employee, linked to whichever
-- Dim_Employee version (employee_key) is CURRENT for that employee.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_load_fact_performance_reviews $$
CREATE PROCEDURE sp_load_fact_performance_reviews()
BEGIN
    INSERT INTO Fact_PerformanceReviews (
        employee_key, department_key, project_key, date_key,
        performance_rating, job_satisfaction, environment_satisfaction,
        relationship_satisfaction, work_life_balance, monthly_income_at_review
    )
    SELECT
        de.employee_key,
        dd.department_key,
        NULL AS project_key,        -- projects are linked separately via assignments
        CAST(DATE_FORMAT(CURRENT_DATE, '%Y%m%d') AS UNSIGNED) AS date_key,
        se.PerformanceRating,
        se.JobSatisfaction,
        se.EnvironmentSatisfaction,
        se.RelationshipSatisfaction,
        se.WorkLifeBalance,
        se.MonthlyIncome
    FROM hr_oltp.staging_employees se
    JOIN Dim_Employee de ON de.employee_id = se.employee_id AND de.is_current = 1
    LEFT JOIN Dim_Department dd ON dd.department_name = se.Department;
END $$

DELIMITER ;

-- ---------------------------------------------------------------------
-- Master ETL run order (call these in this sequence):
--   CALL sp_load_dim_date('2015-01-01', '2027-12-31');
--   CALL sp_load_dim_department();
--   CALL sp_load_dim_project();
--   CALL sp_load_dim_employee_scd2();
--   CALL sp_load_fact_performance_reviews();
-- ---------------------------------------------------------------------
