-- =====================================================================
-- 01_oltp_schema.sql
-- OLTP = "On-Line Transaction Processing" = the normal, day-to-day
-- application database. This is where the Streamlit app writes new
-- employees, projects, and reviews. It is normalized (no repeated data)
-- so it stays fast and consistent for single-record read/writes.
-- OLTP (On-Line Transaction Processing) — the application's operational database.
-- Normalized schema, optimized for single-record reads and writes (onboarding,
-- reviews, project assignments). Run this first on a fresh MySQL server.
--
-- Run this file in MySQL Workbench first, on a fresh schema, e.g.:
--   CREATE DATABASE hr_oltp;
--   CREATE DATABASE IF NOT EXISTS hr_oltp;
--   USE hr_oltp;
--   SOURCE 01_oltp_schema.sql;
-- =====================================================================
--   SOURCE sql/01_oltp_schema.sql;

CREATE DATABASE IF NOT EXISTS hr_oltp;
USE hr_oltp;

-- ---------------------------------------------------------------------
-- Departments: a simple lookup table
-- ---------------------------------------------------------------------
-- Departments: lookup table, referenced by employees and projects.
CREATE TABLE IF NOT EXISTS departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- Employees: the core "one row per person" table.
-- Note: this table only stores the CURRENT state. History lives in the
-- data warehouse (OLAP side), not here — that's the whole point of
-- separating OLTP (current, operational) from OLAP (historical, analytical).
-- ---------------------------------------------------------------------
-- Employees: current state only — one row per person.
-- Historical versions (department moves, promotions) are tracked
-- in the OLAP Dim_Employee table via SCD Type 2.
CREATE TABLE IF NOT EXISTS employees (
    employee_id      INT PRIMARY KEY,               -- comes from the synthesizer
    first_name       VARCHAR(60) NOT NULL,
    last_name        VARCHAR(60) NOT NULL,
    email            VARCHAR(150) NOT NULL UNIQUE,
    employee_id      INT PRIMARY KEY,
    first_name       VARCHAR(60)     NOT NULL,
    last_name        VARCHAR(60)     NOT NULL,
    email            VARCHAR(150)    NOT NULL UNIQUE,
    gender           VARCHAR(10),
    age              INT,
    department_id    INT,
    job_role         VARCHAR(80),
    job_level        INT,
    monthly_income   DECIMAL(10, 2),
    hire_date        DATE,
    attrition        VARCHAR(3),                      -- 'Yes' / 'No'
    attrition        VARCHAR(3),     -- 'Yes' / 'No'
    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ---------------------------------------------------------------------
-- Projects
-- ---------------------------------------------------------------------
-- Projects: belong to a department, optional end date (NULL = ongoing).
CREATE TABLE IF NOT EXISTS projects (
    project_id    INT AUTO_INCREMENT PRIMARY KEY,
    project_name  VARCHAR(150) NOT NULL,
    project_name  VARCHAR(150)    NOT NULL,
    department_id INT,
    start_date    DATE,
    end_date      DATE,
    CONSTRAINT fk_project_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ---------------------------------------------------------------------
-- Assignments: many-to-many link between employees and projects
-- ---------------------------------------------------------------------
-- Assignments: many-to-many link between employees and projects.
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id  INT AUTO_INCREMENT PRIMARY KEY,
    employee_id    INT NOT NULL,
    project_id     INT NOT NULL,
    assignment_id   INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    project_id      INT NOT NULL,
    role_on_project VARCHAR(80),
    assigned_date  DATE DEFAULT (CURRENT_DATE),
    assigned_date   DATE DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_assignment_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    CONSTRAINT fk_assignment_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- ---------------------------------------------------------------------
-- Reviews: performance review submissions (feeds the Fact table later)
-- ---------------------------------------------------------------------
-- Reviews: performance review submissions. Ratings use the 1–4 IBM dataset scale.
-- These rows are later loaded into Fact_PerformanceReviews via the ETL procedures.
CREATE TABLE IF NOT EXISTS reviews (
    review_id            INT AUTO_INCREMENT PRIMARY KEY,
    employee_id           INT NOT NULL,
    review_date           DATE NOT NULL,
    performance_rating    INT,     -- 1-4, matches IBM dataset scale
    job_satisfaction      INT,     -- 1-4
    environment_satisfaction INT,  -- 1-4
    relationship_satisfaction INT, -- 1-4
    work_life_balance     INT,     -- 1-4
    review_id                INT AUTO_INCREMENT PRIMARY KEY,
    employee_id              INT  NOT NULL,
    review_date              DATE NOT NULL,
    performance_rating       INT,
    job_satisfaction         INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    work_life_balance        INT,
    CONSTRAINT fk_review_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- ---------------------------------------------------------------------
-- Staging tables: raw landing zone for the synthesized CSVs before ETL
-- moves cleaned data into the tables above and into the OLAP warehouse.
-- ---------------------------------------------------------------------
-- Staging tables: raw landing zone for the synthesized CSVs.
-- The ETL stored procedures read from here and populate Dim_* and Fact_* tables.
CREATE TABLE IF NOT EXISTS staging_employees (
    employee_id      INT,
    Age              INT,
    Attrition        VARCHAR(3),
    Department       VARCHAR(100),
    DistanceFromHome INT,
    Education        INT,
    EducationField   VARCHAR(100),
    Gender           VARCHAR(10),
    JobLevel         INT,
    JobRole          VARCHAR(100),
    JobSatisfaction  INT,
    EnvironmentSatisfaction INT,
    employee_id              INT,
    Age                      INT,
    Attrition                VARCHAR(3),
    Department               VARCHAR(100),
    DistanceFromHome         INT,
    Education                INT,
    EducationField           VARCHAR(100),
    Gender                   VARCHAR(10),
    JobLevel                 INT,
    JobRole                  VARCHAR(100),
    JobSatisfaction          INT,
    EnvironmentSatisfaction  INT,
    RelationshipSatisfaction INT,
    WorkLifeBalance  INT,
    MonthlyIncome    DECIMAL(10, 2),
    PerformanceRating INT,
    first_name       VARCHAR(60),
    last_name        VARCHAR(60),
    email            VARCHAR(150),
    hire_date        DATE,
    scd_start_date   DATE,
    scd_end_date     DATE,
    is_current       TINYINT
    WorkLifeBalance          INT,
    MonthlyIncome            DECIMAL(10, 2),
    PerformanceRating        INT,
    first_name               VARCHAR(60),
    last_name                VARCHAR(60),
    email                    VARCHAR(150),
    hire_date                DATE,
    scd_start_date           DATE,
    scd_end_date             DATE,
    is_current               TINYINT
);

CREATE TABLE IF NOT EXISTS staging_employee_history (
    employee_id      INT,
    Department       VARCHAR(100),
    JobRole          VARCHAR(100),
    JobLevel         INT,
    MonthlyIncome    DECIMAL(10, 2),
    scd_start_date   DATE,
    scd_end_date     DATE,
    is_current       TINYINT
    employee_id    INT,
    Department     VARCHAR(100),
    JobRole        VARCHAR(100),
    JobLevel       INT,
    MonthlyIncome  DECIMAL(10, 2),
    scd_start_date DATE,
    scd_end_date   DATE,
    is_current     TINYINT
);

-- Helpful indexes for ETL joins/filters
CREATE INDEX idx_staging_emp_id ON staging_employees(employee_id);
CREATE INDEX idx_staging_emp_id  ON staging_employees(employee_id);
CREATE INDEX idx_staging_hist_id ON staging_employee_history(employee_id);
