# OLAP Star Schema

The analytics database (`hr_olap`) uses a classic star schema. One fact table in the centre holds the numbers we want to analyze, and four dimension tables hang off it to provide context (who, what, when, where).

```mermaid
erDiagram
    Dim_Employee {
        int employee_key PK
        int employee_id
        varchar first_name
        varchar last_name
        varchar gender
        int age
        varchar department_name
        varchar job_role
        int job_level
        decimal monthly_income
        varchar attrition
        date start_date
        date end_date
        tinyint is_current
    }

    Dim_Department {
        int department_key PK
        int department_id
        varchar department_name
    }

    Dim_Project {
        int project_key PK
        int project_id
        varchar project_name
        varchar department_name
    }

    Dim_Date {
        int date_key PK
        date full_date
        int day
        int month
        varchar month_name
        int quarter
        int year
    }

    Fact_PerformanceReviews {
        int review_key PK
        int employee_key FK
        int department_key FK
        int project_key FK
        int date_key FK
        int performance_rating
        int job_satisfaction
        int environment_satisfaction
        int relationship_satisfaction
        int work_life_balance
        decimal monthly_income_at_review
    }

    Dim_Employee ||--o{ Fact_PerformanceReviews : "employee_key"
    Dim_Department ||--o{ Fact_PerformanceReviews : "department_key"
    Dim_Project ||--o{ Fact_PerformanceReviews : "project_key"
    Dim_Date ||--o{ Fact_PerformanceReviews : "date_key"
```

**Key points:**
- `Dim_Employee` uses **SCD Type 2** — the same `employee_id` can appear multiple times, each version with a different `employee_key` and date range. Facts always join to the key that was current *at the time of the event*, keeping historical reports accurate.
- `Dim_Date` is pre-populated once (2015–2027) so every fact row always finds a match.
- `monthly_income_at_review` is stored on the fact itself — a snapshot of what the employee was earning when the review was submitted, independent of any later salary changes.

