# System Architecture

This diagram shows the end-to-end data journey — from the raw IBM HR CSV all the way through to the Streamlit dashboard the end user sees.

```mermaid
flowchart TD
    A["IBM HR Attrition CSV\n~1,470 rows"]
    B["Data Synthesizer\nsrc/synthesizer/generate_data.py\nScales to 100k+ rows using Faker + pandas\nInjects SCD Type 2 history"]
    C["Staging Tables\nhr_oltp.staging_employees\nhr_oltp.staging_employee_history"]
    D["OLTP Database — hr_oltp\nemployees · departments\nprojects · assignments · reviews\nNormalized, write-optimized"]
    E["ETL Stored Procedures\nsql/03_etl_procedures.sql\nsp_load_dim_employee_scd2\nsp_load_fact_performance_reviews"]
    F["OLAP Data Warehouse — hr_olap\nDim_Employee (SCD2) · Dim_Department\nDim_Project · Dim_Date\nFact_PerformanceReviews"]
    G["Python DAL\nsrc/db/ · src/models/ · src/managers/\nmysql-connector + python-dotenv"]
    H["Streamlit App — app.py\nOnboard Employee · Projects & Assignments\nSubmit Review · Analytics Dashboard"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    D --> G
    G --> H
```

The app talks to **both** databases at runtime:
- **hr_oltp** — for all write operations (onboarding, reviews, project assignments)
- **hr_olap** — for all read/analytics operations (dashboard charts, SCD2 history)

