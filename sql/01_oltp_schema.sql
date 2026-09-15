-- =====================================================================
-- 01_oltp_schema.sql
-- OLTP = "On-Line Transaction Processing" = the normal, day-to-day
-- application database. This is where the Streamlit app writes new
-- employees, projects, and reviews. It is normalized (no repeated data)
-- so it stays fast and consistent for single-record read/writes.
--
-- Run this file in MySQL Workbench first, on a fresh schema, e.g.:
--   CREATE DATABASE hr_oltp;
--   USE hr_oltp;
--   SOURCE 01_oltp_schema.sql;
-- =====================================================================

CREATE DATABASE IF NOT EXISTS hr_oltp;
USE hr_oltp;

-- ---------------------------------------------------------------------
-- Departments: a simple lookup table
-- ---------------------------------------------------------------------
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
CREATE TABLE IF NOT EXISTS employees (
    employee_id      INT PRIMARY KEY,               -- comes from the synthesizer
    first_name       VARCHAR(60) NOT NULL,
    last_name        VARCHAR(60) NOT NULL,
    email            VARCHAR(150) NOT NULL UNIQUE,
    gender           VARCHAR(10),
    age              INT,
    department_id    INT,
    job_role         VARCHAR(80),
    job_level        INT,
    monthly_income   DECIMAL(10, 2),
    hire_date        DATE,
    attrition        VARCHAR(3),                      -- 'Yes' / 'No'

    -- -----------------------------------------------------------------
    -- Full IBM-dataset column coverage (added so every one of the
    -- original 35 source columns is represented somewhere in the app).
    -- Everything below is a "permanent-ish fact about the person" (same
    -- bucket as age/job_role above) rather than a repeatable per-review
    -- event, which is why these live here and not in `reviews`.
    -- -----------------------------------------------------------------
    employee_number         INT,           -- original IBM row identifier (kept for traceability; employee_id is the real key now)
    business_travel         VARCHAR(30),   -- Non-Travel / Travel_Rarely / Travel_Frequently
    daily_rate               INT,
    distance_from_home       INT,           -- miles/km from home to office
    education                 INT,           -- 1-5 scale
    education_field           VARCHAR(50),
    employee_count            INT,           -- constant in source data (always 1) - kept only for full coverage
    hourly_rate               INT,
    marital_status            VARCHAR(20),
    monthly_rate              INT,
    num_companies_worked      INT,
    over_18                   VARCHAR(3),    -- constant in source data (always 'Y') - kept only for full coverage
    over_time                 VARCHAR(3),    -- 'Yes' / 'No'
    percent_salary_hike       INT,
    standard_hours            INT,           -- constant in source data (always 80) - kept only for full coverage
    stock_option_level        INT,           -- 0-3 scale
    total_working_years       INT,
    years_at_company          INT,
    years_in_current_role     INT,
    years_since_last_promotion INT,
    years_with_curr_manager   INT,

    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS projects (
    project_id    INT AUTO_INCREMENT PRIMARY KEY,
    project_name  VARCHAR(150) NOT NULL,
    department_id INT,
    start_date    DATE,
    end_date      DATE,
    CONSTRAINT fk_project_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ---------------------------------------------------------------------
-- Assignments: many-to-many link between employees and projects
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id  INT AUTO_INCREMENT PRIMARY KEY,
    employee_id    INT NOT NULL,
    project_id     INT NOT NULL,
    role_on_project VARCHAR(80),
    assigned_date  DATE DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_assignment_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    CONSTRAINT fk_assignment_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- ---------------------------------------------------------------------
-- Reviews: performance review submissions (feeds the Fact table later)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    review_id            INT AUTO_INCREMENT PRIMARY KEY,
    employee_id           INT NOT NULL,
    review_date           DATE NOT NULL,
    performance_rating    INT,     -- 1-4, matches IBM dataset scale
    job_satisfaction      INT,     -- 1-4
    environment_satisfaction INT,  -- 1-4
    relationship_satisfaction INT, -- 1-4
    work_life_balance     INT,     -- 1-4
    job_involvement       INT,     -- 1-4 scale, how engaged they felt this cycle
    trainings_last_year   INT,     -- count of trainings completed this cycle
    CONSTRAINT fk_review_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- ---------------------------------------------------------------------
-- Staging tables: raw landing zone for the synthesized CSVs before ETL
-- moves cleaned data into the tables above and into the OLAP warehouse.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging_employees (
    -- This mirrors staging_employees.csv column-for-column (all 35
    -- original IBM columns + the 8 columns the synthesizer added).
    employee_id      INT,
    Age              INT,
    Attrition        VARCHAR(3),
    BusinessTravel   VARCHAR(30),
    DailyRate        INT,
    Department       VARCHAR(100),
    DistanceFromHome INT,
    Education        INT,
    EducationField   VARCHAR(100),
    EmployeeCount    INT,
    EmployeeNumber   INT,
    EnvironmentSatisfaction INT,
    Gender           VARCHAR(10),
    HourlyRate       INT,
    JobInvolvement   INT,
    JobLevel         INT,
    JobRole          VARCHAR(100),
    JobSatisfaction  INT,
    MaritalStatus    VARCHAR(20),
    MonthlyIncome    DECIMAL(10, 2),
    MonthlyRate      INT,
    NumCompaniesWorked INT,
    Over18           VARCHAR(3),
    OverTime         VARCHAR(3),
    PercentSalaryHike INT,
    PerformanceRating INT,
    RelationshipSatisfaction INT,
    StandardHours    INT,
    StockOptionLevel INT,
    TotalWorkingYears INT,
    TrainingTimesLastYear INT,
    WorkLifeBalance  INT,
    YearsAtCompany   INT,
    YearsInCurrentRole INT,
    YearsSinceLastPromotion INT,
    YearsWithCurrManager INT,
    first_name       VARCHAR(60),
    last_name        VARCHAR(60),
    email            VARCHAR(150),
    hire_date        DATE,
    scd_start_date   DATE,
    scd_end_date     DATE,
    is_current       TINYINT
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
);

-- Helpful indexes for ETL joins/filters
CREATE INDEX idx_staging_emp_id ON staging_employees(employee_id);
CREATE INDEX idx_staging_hist_id ON staging_employee_history(employee_id);
