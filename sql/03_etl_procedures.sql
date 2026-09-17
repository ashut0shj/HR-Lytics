USE hr_olap;

DELIMITER $$

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

DROP PROCEDURE IF EXISTS sp_load_dim_employee_scd2 $$
CREATE PROCEDURE sp_load_dim_employee_scd2()
BEGIN
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
        SELECT 1 FROM Dim_Employee de_hist
        WHERE de_hist.employee_id = h.employee_id AND de_hist.is_current = 0
    );

    UPDATE Dim_Employee de_curr
    JOIN hr_oltp.staging_employees se ON se.employee_id = de_curr.employee_id
    SET de_curr.end_date   = DATE_SUB(se.scd_start_date, INTERVAL 1 DAY),
        de_curr.is_current = 0
    WHERE de_curr.is_current = 1
      AND (
            de_curr.department_name <> se.Department
         OR de_curr.job_role        <> se.JobRole
         OR de_curr.job_level       <> se.JobLevel
         OR de_curr.monthly_income  <> se.MonthlyIncome
      );

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
        SELECT 1 FROM Dim_Employee de_new
        WHERE de_new.employee_id = se.employee_id AND de_new.is_current = 1
    );

    -- The two blocks above only cover the initial synthesized/staged load.
    -- Employees onboarded or edited later go straight into hr_oltp.employees
    -- (not the staging tables), so sync from there too on every refresh.
    UPDATE Dim_Employee de_curr
    JOIN hr_oltp.employees oe ON oe.employee_id = de_curr.employee_id
    LEFT JOIN hr_oltp.departments od ON od.department_id = oe.department_id
    SET de_curr.end_date   = DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY),
        de_curr.is_current = 0
    WHERE de_curr.is_current = 1
      AND (
            de_curr.department_name <> od.department_name
         OR de_curr.job_role        <> oe.job_role
         OR de_curr.job_level       <> oe.job_level
         OR de_curr.monthly_income  <> oe.monthly_income
      );

    INSERT INTO Dim_Employee (
        employee_id, first_name, last_name, gender, age,
        department_name, job_role, job_level, monthly_income, attrition,
        start_date, end_date, is_current
    )
    SELECT
        oe.employee_id, oe.first_name, oe.last_name, oe.gender, oe.age,
        od.department_name, oe.job_role, oe.job_level, oe.monthly_income, oe.attrition,
        oe.hire_date, NULL, 1
    FROM hr_oltp.employees oe
    LEFT JOIN hr_oltp.departments od ON od.department_id = oe.department_id
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Employee de_new
        WHERE de_new.employee_id = oe.employee_id AND de_new.is_current = 1
    );
END $$

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
        NULL AS project_key,
        dt.date_key,
        se.PerformanceRating,
        se.JobSatisfaction,
        se.EnvironmentSatisfaction,
        se.RelationshipSatisfaction,
        se.WorkLifeBalance,
        se.MonthlyIncome
    FROM hr_oltp.staging_employees se
    JOIN Dim_Employee de    ON de.employee_id = se.employee_id AND de.is_current = 1
    JOIN Dim_Date dt        ON dt.full_date = se.hire_date
    LEFT JOIN Dim_Department dd ON dd.department_name = se.Department;
END $$

-- new employees added directly to hr_oltp.employees (not via CSV staging)
DROP PROCEDURE IF EXISTS sp_load_dim_employee_incremental $$
CREATE PROCEDURE sp_load_dim_employee_incremental()
BEGIN
    INSERT INTO Dim_Employee (
        employee_id, first_name, last_name, gender, age,
        department_name, job_role, job_level, monthly_income, attrition,
        start_date, end_date, is_current
    )
    SELECT
        e.employee_id, e.first_name, e.last_name, e.gender, e.age,
        d.department_name, e.job_role, e.job_level, e.monthly_income, e.attrition,
        e.hire_date, NULL, 1
    FROM hr_oltp.employees e
    LEFT JOIN hr_oltp.departments d ON d.department_id = e.department_id
    WHERE NOT EXISTS (
        SELECT 1 FROM Dim_Employee de
        WHERE de.employee_id = e.employee_id
    );
END $$

-- loads reviews submitted from the app (hr_oltp.reviews) into the fact table
DROP PROCEDURE IF EXISTS sp_load_fact_reviews_incremental $$
CREATE PROCEDURE sp_load_fact_reviews_incremental()
BEGIN
    INSERT INTO Fact_PerformanceReviews (
        employee_key, department_key, project_key, date_key,
        performance_rating, job_satisfaction, environment_satisfaction,
        relationship_satisfaction, work_life_balance, monthly_income_at_review
    )
    SELECT
        de.employee_key,
        dd.department_key,
        NULL AS project_key,
        dt.date_key,
        r.performance_rating,
        r.job_satisfaction,
        r.environment_satisfaction,
        r.relationship_satisfaction,
        r.work_life_balance,
        e.monthly_income
    FROM hr_oltp.reviews r
    JOIN hr_oltp.employees e   ON e.employee_id = r.employee_id
    JOIN Dim_Employee de       ON de.employee_id = r.employee_id AND de.is_current = 1
    JOIN Dim_Date dt           ON dt.full_date = r.review_date
    LEFT JOIN hr_oltp.departments d ON d.department_id = e.department_id
    LEFT JOIN Dim_Department dd     ON dd.department_name = d.department_name
    WHERE NOT EXISTS (
        SELECT 1 FROM Fact_PerformanceReviews f
        WHERE f.employee_key = de.employee_key
          AND f.date_key = dt.date_key
    );
END $$

DELIMITER ;