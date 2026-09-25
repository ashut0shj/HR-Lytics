CREATE DATABASE IF NOT EXISTS hr_oltp;
USE hr_oltp;

CREATE TABLE IF NOT EXISTS departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id      INT PRIMARY KEY,
    first_name       VARCHAR(60)     NOT NULL CHECK (first_name REGEXP '^[A-Za-z]+$'),
    last_name        VARCHAR(60)     NOT NULL CHECK (last_name REGEXP '^[A-Za-z]+$'),
    email             VARCHAR(150)    NOT NULL UNIQUE,
    gender           VARCHAR(10),
    age              INT,
    department_id    INT,
    job_role         VARCHAR(80),
    job_level        INT,
    monthly_income   DECIMAL(10, 2),
    hire_date        DATE,
    attrition        VARCHAR(3),
    employee_number          INT,
    business_travel          VARCHAR(30),
    daily_rate                DECIMAL(10, 2),
    distance_from_home       INT,
    education                INT,
    education_field          VARCHAR(50),
    employee_count           INT,
    hourly_rate                DECIMAL(10, 2),
    marital_status            VARCHAR(20),
    monthly_rate                DECIMAL(10, 2),
    num_companies_worked     INT,
    over_18                  VARCHAR(3),
    over_time                VARCHAR(3),
    percent_salary_hike      INT,
    standard_hours           INT,
    stock_option_level       INT,
    total_working_years      INT,
    years_at_company         INT,
    years_in_current_role    INT,
    years_since_last_promotion INT,
    years_with_curr_manager  INT,
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

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id   INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    project_id      INT NOT NULL,
    role_on_project VARCHAR(80),
    assigned_date   DATE DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_assignment_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    CONSTRAINT fk_assignment_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id                INT AUTO_INCREMENT PRIMARY KEY,
    employee_id              INT  NOT NULL,
    review_date              DATE NOT NULL,
    performance_rating       INT,
    job_satisfaction         INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    work_life_balance        INT,
    job_involvement          INT,
    trainings_last_year      INT,
    CONSTRAINT fk_review_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS staging_employees (
    employee_id              INT PRIMARY KEY,
    Age                      INT,
    Attrition                VARCHAR(3),
    BusinessTravel           VARCHAR(30),
    DailyRate                DECIMAL(10, 2),
    Department               VARCHAR(100),
    DistanceFromHome         INT,
    Education                INT,
    EducationField           VARCHAR(100),
    EmployeeCount            INT,
    EmployeeNumber           INT,
    EnvironmentSatisfaction  INT,
    Gender                   VARCHAR(10),
    HourlyRate               DECIMAL(10, 2),
    JobInvolvement           INT,
    JobLevel                 INT,
    JobRole                  VARCHAR(100),
    JobSatisfaction          INT,
    MaritalStatus            VARCHAR(20),
    MonthlyIncome            DECIMAL(10, 2),
    MonthlyRate               DECIMAL(10, 2),
    NumCompaniesWorked       INT,
    Over18                   VARCHAR(3),
    OverTime                 VARCHAR(3),
    PercentSalaryHike        INT,
    PerformanceRating        INT,
    RelationshipSatisfaction INT,
    StandardHours            INT,
    StockOptionLevel         INT,
    TotalWorkingYears        INT,
    TrainingTimesLastYear    INT,
    WorkLifeBalance          INT,
    YearsAtCompany           INT,
    YearsInCurrentRole       INT,
    YearsSinceLastPromotion  INT,
    YearsWithCurrManager     INT,
    first_name               VARCHAR(60),
    last_name                VARCHAR(60),
    email                    VARCHAR(150),
    hire_date                DATE,
    scd_start_date           DATE,
    scd_end_date              DATE,
    is_current               TINYINT
);

CREATE TABLE IF NOT EXISTS staging_employee_history (
    staging_hist_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_id      INT,
    Department       VARCHAR(100),
    JobRole          VARCHAR(100),
    JobLevel         INT,
    MonthlyIncome    DECIMAL(10, 2),
    scd_start_date   DATE,
    scd_end_date     DATE,
    is_current       TINYINT
);

CREATE INDEX idx_staging_emp_id  ON staging_employees(employee_id);
CREATE INDEX idx_staging_hist_id ON staging_employee_history(employee_id);
