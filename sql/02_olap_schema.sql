-- =====================================================================
-- 02_olap_schema.sql
-- OLAP = "On-Line Analytical Processing" = the Data Warehouse.
-- This uses a STAR SCHEMA: one Fact table in the middle (the numbers we
-- want to analyze) surrounded by Dimension tables (the "who/what/when"
-- context that lets us slice those numbers).
--
--            Dim_Employee     Dim_Department
--                   \             /
--                    \           /
--                  Fact_PerformanceReviews
--                    /           \
--                   /             \
--            Dim_Project        Dim_Date
--
-- Run this AFTER 01_oltp_schema.sql, e.g.:
--   CREATE DATABASE hr_olap;
--   USE hr_olap;
--   SOURCE 02_olap_schema.sql;
-- =====================================================================

CREATE DATABASE IF NOT EXISTS hr_olap;
USE hr_olap;

-- ---------------------------------------------------------------------
-- Dim_Date: a standard "date dimension" so we can group facts by year,
-- quarter, month, etc. without doing date math at query time.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Dim_Date (
    date_key    INT PRIMARY KEY,        -- surrogate key, format YYYYMMDD
    full_date   DATE NOT NULL,
    day         INT,
    month       INT,
    month_name  VARCHAR(20),
    quarter     INT,
    year        INT
);

-- ---------------------------------------------------------------------
-- Dim_Department
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Dim_Department (
    department_key   INT AUTO_INCREMENT PRIMARY KEY,  -- surrogate key
    department_id    INT,                             -- business key (from OLTP)
    department_name  VARCHAR(100)
);

-- ---------------------------------------------------------------------
-- Dim_Project
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Dim_Project (
    project_key   INT AUTO_INCREMENT PRIMARY KEY,     -- surrogate key
    project_id    INT,                                -- business key
    project_name  VARCHAR(150),
    department_name VARCHAR(100)
);

-- ---------------------------------------------------------------------
-- Dim_Employee: THIS is the SCD Type 2 table.
--
-- Every time an employee's department / job role / job level / salary
-- changes, instead of UPDATING the row, we INSERT a new row and:
--   - close the OLD row by setting end_date = day before the change,
--     is_current = 0
--   - the NEW row gets start_date = day of the change, end_date = NULL,
--     is_current = 1
--
-- This means the SAME employee_id can appear multiple times here, each
-- with a different employee_key (surrogate key). Facts always link to
-- the specific employee_key that was current AT THE TIME of the fact,
-- so historical reports stay accurate even after someone gets promoted.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Dim_Employee (
    employee_key    INT AUTO_INCREMENT PRIMARY KEY,   -- surrogate key (unique per version)
    employee_id     INT NOT NULL,                     -- business key (same across versions)
    first_name      VARCHAR(60),
    last_name       VARCHAR(60),
    gender          VARCHAR(10),
    age             INT,
    department_name VARCHAR(100),
    job_role        VARCHAR(100),
    job_level       INT,
    monthly_income  DECIMAL(10, 2),
    attrition       VARCHAR(3),
    start_date      DATE NOT NULL,   -- when this version became true
    end_date        DATE NULL,       -- NULL means "still true" (current)
    is_current      TINYINT NOT NULL DEFAULT 1
);

CREATE INDEX idx_dim_employee_bkey ON Dim_Employee(employee_id);
CREATE INDEX idx_dim_employee_current ON Dim_Employee(is_current);

-- ---------------------------------------------------------------------
-- Fact_PerformanceReviews: the numeric facts we analyze.
-- One row = one performance review event, linked to the dimension
-- version that was CURRENT on the review date.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Fact_PerformanceReviews (
    review_key       INT AUTO_INCREMENT PRIMARY KEY,
    employee_key      INT NOT NULL,          -- FK -> Dim_Employee.employee_key
    department_key    INT,                   -- FK -> Dim_Department.department_key
    project_key       INT,                   -- FK -> Dim_Project.project_key (nullable)
    date_key          INT NOT NULL,          -- FK -> Dim_Date.date_key

    performance_rating INT,
    job_satisfaction    INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    work_life_balance   INT,
    monthly_income_at_review DECIMAL(10, 2),

    CONSTRAINT fk_fact_employee
        FOREIGN KEY (employee_key) REFERENCES Dim_Employee(employee_key),
    CONSTRAINT fk_fact_department
        FOREIGN KEY (department_key) REFERENCES Dim_Department(department_key),
    CONSTRAINT fk_fact_project
        FOREIGN KEY (project_key) REFERENCES Dim_Project(project_key),
    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key) REFERENCES Dim_Date(date_key)
);

CREATE INDEX idx_fact_employee ON Fact_PerformanceReviews(employee_key);
CREATE INDEX idx_fact_date ON Fact_PerformanceReviews(date_key);
