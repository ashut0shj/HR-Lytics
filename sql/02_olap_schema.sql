CREATE DATABASE IF NOT EXISTS hr_olap;
USE hr_olap;

CREATE TABLE IF NOT EXISTS Dim_Date (
    date_key   INT PRIMARY KEY,
    full_date  DATE NOT NULL,
    day        INT,
    month      INT,
    month_name VARCHAR(20),
    quarter    INT,
    year       INT
);

ALTER TABLE Dim_Date ADD UNIQUE INDEX idx_dim_date_full_date (full_date);

CREATE TABLE IF NOT EXISTS Dim_Department (
    department_key  INT AUTO_INCREMENT PRIMARY KEY,
    department_id   INT,
    department_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Dim_Project (
    project_key     INT AUTO_INCREMENT PRIMARY KEY,
    project_id      INT,
    project_name    VARCHAR(150),
    department_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Dim_Employee (
    employee_key    INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    first_name      VARCHAR(60),
    last_name       VARCHAR(60),
    gender          VARCHAR(10),
    age             INT,
    department_name VARCHAR(100),
    job_role        VARCHAR(100),
    job_level       INT,
    monthly_income  DECIMAL(10, 2),
    attrition       VARCHAR(3),
    start_date      DATE NOT NULL,
    end_date        DATE NULL,
    is_current      TINYINT NOT NULL DEFAULT 1
);

CREATE INDEX idx_dim_employee_bkey    ON Dim_Employee(employee_id);
CREATE INDEX idx_dim_employee_current ON Dim_Employee(is_current);

CREATE TABLE IF NOT EXISTS Fact_PerformanceReviews (
    review_key                INT AUTO_INCREMENT PRIMARY KEY,
    employee_key              INT NOT NULL,
    department_key            INT,
    project_key               INT,
    date_key                  INT NOT NULL,
    performance_rating        INT,
    job_satisfaction          INT,
    environment_satisfaction  INT,
    relationship_satisfaction INT,
    work_life_balance         INT,
    monthly_income_at_review  DECIMAL(10, 2),
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
CREATE INDEX idx_fact_date     ON Fact_PerformanceReviews(date_key);
