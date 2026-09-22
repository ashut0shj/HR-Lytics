# HR-Lytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://v4c-lytic.streamlit.app/)  
**Live Application:** [https://v4c-lytic.streamlit.app/](https://v4c-lytic.streamlit.app/)

HR-Lytics is an enterprise HR analytics and operational platform built with Python, MySQL, and Streamlit. It implements a dual-database architecture separating daily transactional operations (OLTP) from reporting and analytics (OLAP data warehouse with SCD Type 2 history).

* **OLTP (`hr_oltp`)**: Normalized database for day-to-day operations — employee onboarding, department tracking, project assignments, and performance reviews.
* **OLAP (`hr_olap`)**: Star schema data warehouse with SCD Type 2 dimension tracking and fact tables for analytics dashboards.

Data flows from OLTP $\rightarrow$ OLAP via automated ETL stored procedures.

---

## System Architecture

```mermaid
flowchart TD
    A["IBM HR Attrition CSV\n~1,470 rows"] --> B["Data Synthesizer\nsrc/generate_data.py\nScales to 100k+ rows using Faker + pandas\nInjects SCD Type 2 history"]
    B --> C["Staging Tables\nhr_oltp.staging_employees\nhr_oltp.staging_employee_history"]
    C --> D["OLTP Database — hr_oltp\nemployees · departments\nprojects · assignments · reviews\nNormalized, write-optimized"]
    D --> E["ETL Stored Procedures\nsql/03_etl_procedures.sql\nsp_load_dim_employee_scd2\nsp_load_fact_performance_reviews"]
    E --> F["OLAP Data Warehouse — hr_olap\nDim_Employee (SCD2) · Dim_Department\nDim_Project · Dim_Date\nFact_PerformanceReviews"]
    D --> G["Python DAL\nsrc/db_wrapper.py · src/models.py · src/managers.py"]
    F --> G
    G --> H["Streamlit App — app.py\nAnalytics Dashboard · Onboard Employee\nProjects & Assignments · Submit Review · Data Explorer"]
```

---

## Data Models

### OLTP Entity-Relationship Diagram (`hr_oltp`)

```mermaid
erDiagram
    departments ||--o{ employees : "has"
    departments ||--o{ projects : "owns"
    employees ||--o{ assignments : "assigned via"
    projects ||--o{ assignments : "includes"
    employees ||--o{ reviews : "receives"

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
```

### OLAP Star Schema (`hr_olap`)

```mermaid
flowchart TD
    subgraph Dimensions
        D1["Dim_Employee\n(SCD Type 2)\nemployee_key (PK)\nemployee_id\ndepartment_name\njob_role\nmonthly_income\nstart_date / end_date\nis_current"]
        D2["Dim_Department\ndepartment_key (PK)\ndepartment_id\ndepartment_name"]
        D3["Dim_Project\nproject_key (PK)\nproject_id\nproject_name"]
        D4["Dim_Date\ndate_key (PK)\nfull_date\nyear / month / quarter"]
    end

    subgraph Facts
        F1["Fact_PerformanceReviews\nreview_key (PK)\nemployee_key (FK)\ndepartment_key (FK)\nproject_key (FK)\ndate_key (FK)\nperformance_rating\njob_satisfaction\nenvironment_satisfaction\nwork_life_balance"]
    end

    D1 --> F1
    D2 --> F1
    D3 --> F1
    D4 --> F1
```

---

## Slowly Changing Dimension (SCD Type 2) Flow

When an employee changes departments or roles, the existing record is closed with an `end_date` and `is_current = 0`, while a new record is created with `is_current = 1`:

```mermaid
flowchart LR
    A["Employee Department Change\n(e.g., Sales → R&D)"] --> B["Close Current Record\nis_current = 0\nend_date = today"]
    B --> C["Insert New Record\nis_current = 1\nstart_date = today\nend_date = NULL\nnew department_name"]
```

---

## Project Structure

```text
HR-Lytics/
├── migrate.py                  # One-shot migration & ETL runner (uses DBWrapper)
├── app.py                      # Streamlit interactive application
├── requirements.txt            # Python dependencies
├── .env.example                # Template for database configuration
├── src/
│   ├── db_wrapper.py           # MySQL connection management & pooling
│   ├── generate_data.py        # Synthetic dataset generation with SCD2 history
│   ├── managers.py             # Data access layer & business logic
│   ├── models.py               # Dataclass entities (Employee, Project, Review)
│   └── query_loader.py         # Dynamic SQL query loader from sql/ files
├── sql/
│   ├── 01_oltp_schema.sql      # DDL for hr_oltp tables
│   ├── 02_olap_schema.sql      # DDL for hr_olap star schema
│   ├── 03_etl_procedures.sql   # Stored procedures for ETL pipeline
│   ├── 04_analytics_queries.sql# Standalone analytics SQL queries
│   ├── oltp/                   # Modular OLTP CRUD SQL statements
│   └── olap/                   # Modular OLAP analytics SQL statements
├── diagrams/                   # Raw architecture & schema markdown diagrams
└── dataset/                    # Source IBM HR CSV & staging files
```

---

## Setup & Installation

**Prerequisites:** Python 3.10+, MySQL server (e.g., local MySQL or cloud instance like Aiven).

```bash
git clone https://github.com/ashut0shj/HR-Lytics.git
cd HR-Lytics
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your connection details:

```bash
cp .env.example .env
```

```ini
DB_HOST=your-mysql-host
DB_USER=your-user
DB_PASSWORD=your-password
DB_NAME=hr_oltp
DB_PORT=3306
```

---

## Running Migration & Launching the App

### 1. Run Migration (First-time Setup)
Run `migrate.py` to generate synthetic data, create schemas, load staging tables, and execute the initial OLAP ETL:

```bash
python migrate.py
```

### 2. Start the Streamlit App
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

---

## Key App Features

* **Analytics Dashboard**: Real-time metrics, department headcount, attrition analysis, salary distribution, YoY trends, top performers (window functions), and SCD Type 2 audit history.
* **Onboard Employee**: Add new employees into `hr_oltp` and manage department transfers.
* **Projects & Assignments**: Manage company projects and assign staff.
* **Submit Review**: Record satisfaction & performance review ratings.
* **Data Explorer**: Live interactive query & filter tool for operational tables.
* **Refresh OLAP Button**: Syncs operational changes from OLTP to the OLAP data warehouse on demand.
