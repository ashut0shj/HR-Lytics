# OLTP Entity-Relationship Diagram

The operational database (`hr_oltp`) is normalized for fast, consistent read/write operations. Each table stores one thing and one thing only.

```mermaid
erDiagram
    departments {
        int department_id PK
        varchar department_name
    }

    employees {
        int employee_id PK
        varchar first_name
        varchar last_name
        varchar email
        varchar gender
        int age
        int department_id FK
        varchar job_role
        int job_level
        decimal monthly_income
        date hire_date
        varchar attrition
        int employee_number
        varchar business_travel
        int daily_rate
        int distance_from_home
        int education
        varchar education_field
        int employee_count
        int hourly_rate
        varchar marital_status
        int monthly_rate
        int num_companies_worked
        varchar over_18
        varchar over_time
        int percent_salary_hike
        int standard_hours
        int stock_option_level
        int total_working_years
        int years_at_company
        int years_in_current_role
        int years_since_last_promotion
        int years_with_curr_manager
    }

    projects {
        int project_id PK
        varchar project_name
        int department_id FK
        date start_date
        date end_date
    }

    assignments {
        int assignment_id PK
        int employee_id FK
        int project_id FK
        varchar role_on_project
        date assigned_date
    }

    reviews {
        int review_id PK
        int employee_id FK
        date review_date
        int performance_rating
        int job_satisfaction
        int environment_satisfaction
        int relationship_satisfaction
        int work_life_balance
    }

    staging_employees {
        int employee_id
        varchar first_name
        varchar last_name
        varchar email
        date hire_date
        date scd_start_date
        date scd_end_date
        tinyint is_current
    }

    departments ||--o{ employees : "has"
    departments ||--o{ projects : "owns"
    employees ||--o{ assignments : "assigned via"
    projects ||--o{ assignments : "includes"
    employees ||--o{ reviews : "receives"
    staging_employees ||--o| employees : "loads into"
```

**Key design decisions:**
- `employees` only stores the *current* state. Historical versions live in `Dim_Employee` (OLAP side) via SCD Type 2.
- `assignments` is the many-to-many bridge between employees and projects.
- Ratings use a 1–4 integer scale matching the original IBM dataset.
