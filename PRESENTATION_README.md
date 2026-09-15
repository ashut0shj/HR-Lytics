# HR-Lytics — Enterprise HR Analytics & Data Platform

HR-Lytics is an end-to-end HR data engineering and analytics solution. It models employee lifecycles, performance metrics, and departmental structures through a dual-database architecture: a normalized OLTP operational database paired with a star-schema analytical warehouse featuring Slowly Changing Dimensions (SCD Type 2).

The platform includes operational workflows for employee onboarding, project assignments, and performance evaluations, coupled with an executive analytics dashboard built on Streamlit.

---

## Executive Summary & Highlights

* **Dual-Tier Database Architecture**: Separation of concerns between transactional daily operations (`hr_oltp`) and read-heavy reporting queries (`hr_olap`).
* **SCD Type 2 Historical Tracking**: Preserves complete employee career histories (department changes, promotions, compensation shifts) over time without overwriting prior records.
* **Automated Data Synthesis & Scaling**: Capability to scale base workforce records to 100,000+ realistic profiles using Faker and Pandas to simulate enterprise data volumes.
* **SQL Window Functions & Advanced KPIs**: Department-level rankings via `DENSE_RANK()`, attrition risk categorization using `NTILE()`, and longitudinal performance trends.
* **Streamlit Operational Portal & Dashboard**: Web interface for both day-to-day HR workflows (onboarding, reviews, projects) and business intelligence charts.

---

## Core Capabilities

### 1. Executive Analytics Dashboard
* **Workforce Overview**: Real-time metrics covering active headcount, company-wide attrition rate, and average monthly income.
* **Departmental Distribution**: Interactive breakdowns of workforce distribution across business units.
* **Attrition Analysis**: Correlation between compensation, roles, and employee turnover.
* **Performance Trends**: Multi-year trends tracking performance ratings and job satisfaction scores.
* **Top Performers Ranking**: Identifies top performers within each department using SQL window functions (`DENSE_RANK()`).
* **SCD Type 2 Audit Trail**: Dedicated historical view displaying employee movements across departments with effective validity dates.

### 2. Operational HR Management
* **Employee Onboarding**: Form-driven creation of employee profiles tied to active departments, auto-calculating initial IDs and career parameters.
* **Department Transfers (SCD2)**: Facilitates internal mobility; when an employee switches departments, the system automatically closes out the old record version and registers the new state.
* **Project Allocation**: Setup of business projects with timeline management and cross-functional team assignments.
* **Performance Review Submissions**: Multi-dimensional evaluation forms assessing job satisfaction, environment satisfaction, work-life balance, and performance ratings (1–4 scale).

---

## Technical Architecture Overview

The system operates across three tiers:

1. **Operational Layer (OLTP)**: Normalized relational schema (`hr_oltp`) housing active employees, departments, projects, assignments, and raw review logs.
2. **Analytical Warehouse (OLAP)**: Star schema (`hr_olap`) comprising dimension tables (`Dim_Employee`, `Dim_Department`, `Dim_Project`, `Dim_Date`) and a central fact table (`Fact_PerformanceReviews`).
3. **Data Access & Presentation Layer**:
   * **Data Access Layer (DAL)**: Python OOP architecture with entity models and manager classes managing transactions and analytics retrieval.
   * **Application Layer**: Interactive Streamlit interface visualizing datasets with Plotly.

> Comprehensive entity-relationship models, star-schema designs, SCD2 workflows, and ETL pipeline documentation are cataloged in the [`diagrams/`](diagrams/) directory.

---

## Project Structure

```text
HR-Lytics/
├── app.py                     # Streamlit application entry point
├── requirements.txt           # Project dependencies
├── .env.example               # Environment variables configuration template
├── src/
│   ├── db/
│   │   ├── db_wrapper.py      # Database connection handling & query execution
│   │   └── query_loader.py    # SQL query loader
│   ├── managers/
│   │   └── managers.py        # Business logic & Data Access Layer (DAL)
│   ├── models/
│   │   └── models.py          # Domain entities (Employee, Project, Review)
│   └── synthesizer/
│       └── generate_data.py   # Dataset generator & historical synthesizer
├── sql/
│   ├── 01_oltp_schema.sql     # DDL for operational database (hr_oltp)
│   ├── 02_olap_schema.sql     # DDL for star schema data warehouse (hr_olap)
│   ├── 03_etl_procedures.sql  # Stored procedures for warehouse loading & SCD2
│   ├── 04_analytics_queries.sql # Window function & KPI query definitions
│   ├── oltp/                  # Parameterized operational queries
│   └── olap/                  # Parameterized reporting queries
├── diagrams/                  # System design specifications & Mermaid diagrams
├── dataset/                   # Source data files
└── Planning_docs/             # Architectural specifications & planning notes
```

---

## Getting Started

### 1. Environment Configuration

Clone the repository and install required packages:

```bash
git clone <repository-url>
cd HR-Lytics

python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` configuration in the project root:

```bash
cp .env.example .env
```

Ensure the credentials reflect your MySQL instance:

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hr_oltp
DB_PORT=3306
```

### 2. Database Initialization

Execute the SQL initialization scripts sequentially against your MySQL server:

```sql
-- Step 1: Create OLTP schema and tables
SOURCE sql/01_oltp_schema.sql;

-- Step 2: Create OLAP star schema
SOURCE sql/02_olap_schema.sql;

-- Step 3: Compile ETL stored procedures
SOURCE sql/03_etl_procedures.sql;
```

### 3. (Optional) Synthetic Data Generation & Loading

To populate the warehouse with scaled enterprise records (100k+ employees):

1. Ensure the IBM HR attrition dataset (`WA_Fn-UseC_-HR-Employee-Attrition.csv`) is placed in `dataset/`.
2. Generate the synthesized records:
   ```bash
   python src/synthesizer/generate_data.py
   ```
3. Load the generated staging files (`staging_employees.csv` and `staging_employee_history.csv`) into their respective staging tables, then trigger the ETL pipeline:
   ```sql
   CALL sp_load_dim_date('2015-01-01', '2027-12-31');
   CALL sp_load_dim_department();
   CALL sp_load_dim_project();
   CALL sp_load_dim_employee_scd2();
   CALL sp_load_fact_performance_reviews();
   ```

### 4. Launching the Application

Run the Streamlit web dashboard:

```bash
streamlit run app.py
```

Access the interface in your browser at `http://localhost:8501`.

---

## Technology Stack

* **Programming Language**: Python 3.10+
* **Framework & UI**: Streamlit, Plotly Express
* **Database Management**: MySQL 8.0+ (`mysql-connector-python`)
* **Data Processing & Engineering**: Pandas, NumPy
* **Synthetic Generation**: Faker
* **Configuration**: Python-Dotenv

