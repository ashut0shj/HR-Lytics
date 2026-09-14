# HR-Lytics — Enterprise Employee Analytics & Data Warehouse
# HR-Lytics

HR-Lytics is an end-to-end Data Engineering and Analytics platform developed as part of the **V4C Data Engineering Training Exercise**. It demonstrates data synthesis, OLTP database modeling, OLAP star schema dimensional modeling with Slowly Changing Dimensions (SCD Type 2), Python OOP Data Access Layer, and an interactive Streamlit analytics dashboard.
An HR analytics web app built with Streamlit and MySQL. It lets you manage employees, projects, and performance reviews through a simple UI, and shows analytics dashboards backed by a star-schema data warehouse.
An end-to-end HR analytics platform built as part of the **V4C Data Engineering Training Exercise**. It covers the full stack: synthetic data generation, a normalized OLTP database, a star-schema data warehouse with SCD Type 2 history tracking, an ETL pipeline via MySQL stored procedures, and a Streamlit dashboard for both operational data entry and executive-level analytics.

---

## 🏗️ System Architecture & Data Flow
## What it does

The app has four sections:

- **Analytics Dashboard** — headcount by department, attrition rate, year-over-year performance trends, top performers per department (using SQL window functions), average salary by job role, and SCD Type 2 department-change history.
- **Onboard Employee** — add a new employee, assign them to a department, and apply SCD2 department transfers with full history preserved.
- **Projects & Assignments** — create projects and assign employees to them with a specific role.
- **Submit Review** — log performance reviews (ratings 1–4 across 5 dimensions) and view an employee's full review history.

---

## Architecture

```mermaid
flowchart TD
    A["IBM HR Analytics CSV (~1,470 rows)"] --> B["Data Synthesizer (Python / pandas / Faker)"]
    B --> C["MySQL Staging & OLTP DB (System of Record)"]
    C -->|ETL: Stored Procedures / Window Fns| D["MySQL OLAP Star Schema (SCD Type 2)"]
    D --> E["Python OOP Data Access Layer (DAL)"]
    E --> F["Streamlit Web Application (Dashboards & Forms)"]
    A["IBM HR Attrition CSV"] --> B["Data Synthesizer\npandas + Faker → 100k rows"]
    B --> C["MySQL Staging Tables\nhr_oltp"]
    C --> D["ETL Stored Procedures"]
    D --> E["OLAP Star Schema\nhr_olap — Dim_Employee (SCD2)\nFact_PerformanceReviews"]
    E --> F["Python DAL\nsrc/managers · src/models · src/db"]
    C --> F
    F --> G["Streamlit App\napp.py"]
```
- **Onboard employees** — add new staff, assign them to departments
- **Projects & assignments** — create projects and assign employees to them
- **Performance reviews** — submit and view review scores
- **Analytics dashboard** — headcount, attrition rate, salary breakdowns, year-over-year trends, top performers per department, and SCD Type 2 change history

The app runs against two MySQL databases:
- **OLTP** (`training`) — the live operational tables: `employees`, `departments`, `projects`, `reviews`, `assignments`
- **OLAP** (star schema) — `Dim_Employee`, `Dim_Date`, `Fact_PerformanceReviews` — populated via the ETL procedures in `sql/`
The app reads analytics from `hr_olap` and writes operational data to `hr_oltp`. See the [`diagrams/`](diagrams/) folder for detailed Mermaid diagrams of the ER model, star schema, SCD2 flow, and ETL pipeline.

---

## 🛠️ Quick Setup & Environment
## Project layout

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```
```
HR-Lytics/
├── app.py                  # Streamlit app entry point
├── app.py                        # Streamlit entry point
├── requirements.txt
├── .env                    # DB credentials (not committed)
├── .env.example                  # Copy to .env and fill in your DB credentials
├── src/
│   ├── db/
│   │   ├── db_wrapper.py   # MySQL connection wrapper
│   │   └── query_loader.py # Loads named queries from .sql files
│   │   ├── db_wrapper.py         # MySQL connection wrapper (auto-reconnect)
│   │   └── query_loader.py       # Loads named queries from .sql files
│   ├── managers/
│   │   └── managers.py     # CRUD + analytics logic
│   │   └── managers.py           # CRUD + analytics logic (one class per entity)
│   ├── models/
│   │   └── models.py       # Employee, Project, Review dataclasses
│   │   └── models.py             # Employee, Project, Review dataclasses
│   └── synthesizer/
│       └── generate_data.py  # Generates 100k+ synthetic HR rows
│       └── generate_data.py      # Scales IBM CSV to 100k rows, builds SCD2 history
├── sql/
│   ├── oltp/               # employees, departments, projects, reviews queries
│   ├── olap/               # analytics queries (window functions, SCD2)
│   ├── 01_oltp_schema.sql  # Create OLTP tables
│   ├── 02_olap_schema.sql  # Create star schema tables
│   ├── 03_etl_procedures.sql
│   └── 04_analytics_queries.sql
└── dataset/                # Put the IBM HR CSV here
│   ├── 01_oltp_schema.sql        # Create OLTP tables (run first)
│   ├── 02_olap_schema.sql        # Create star schema tables (run second)
│   ├── 03_etl_procedures.sql     # Stored procedures to populate the warehouse
│   ├── 04_analytics_queries.sql  # Standalone analytics queries (reference)
│   ├── oltp/                     # Named queries used by the Python DAL
│   └── olap/                     # Named analytics queries used by the DAL
├── diagrams/                     # Architecture diagrams (Mermaid, .md files)
├── dataset/                      # Put the IBM HR CSV here before synthesizing
└── Planning_docs/                # Internal design docs from the planning phase
```

2. **Activate virtual environment:**
   - **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   - **Linux/macOS:** `source venv/bin/activate`
---

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
## Setup

---
**1. Clone and create a virtual environment**
### 1. Clone and set up a virtual environment

##  File Placement & Folder Guide
```bash
git clone <repo-url>
cd HR-Lytics
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Use this guide to determine where to create and place files within the repository:
**2. Set up your `.env` file**
### 2. Configure your database connection

```text
HR-Lytics/
├── data/
│   ├── raw/                       # Place original untouched source CSVs (e.g. ibm_hr_attrition.csv)
│   └── synthesized/               # Place scaled output datasets (e.g. employees_100k.csv)
├── sql/
│   ├── oltp/                      # Relational OLTP DDL, DML, constraints & index scripts
│   ├── olap/                      # Star schema DDL scripts (dimension & fact tables)
│   ├── etl/                       # Stored procedures (sp_*), CTEs, & SCD2 merge scripts
│   └── analytics/                 # Analytical & KPI queries (window functions, dense rank)
├── src/
│   ├── synthesizer/               # Python scripts for scaling data & SCD2 history injection
│   ├── db/                        # Singleton DatabaseConnection handlers
│   ├── models/                    # Entity classes (Employee, Project, Review)
│   ├── managers/                  # Data Access Layer (DAL) manager classes
│   └── etl/                       # Python ETL orchestration scripts
├── app/
│   ├── Home.py                    # Streamlit home landing page
│   └── pages/                     # Streamlit multi-page forms and dashboard views
├── diagrams/                      # ER diagrams, dimensional models (Draw.io, PNG exports)
└── tests/                         # Pytest unit & integration test scripts
Create a `.env` file in the project root:
Copy `.env.example` to `.env` and fill in your MySQL credentials:

```bash
cp .env.example .env
```

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=training
DB_NAME=hr_oltp
DB_PORT=3306
```

---
**3. Set up the database**
> The app reads `hr_oltp` for operational data and `hr_olap` for analytics. Both databases need to exist on the same MySQL server.

## 🚀 Key Modules & Capabilities
Run the SQL files in MySQL Workbench (or any client) in order:
### 3. Create the database schemas

1. **Data Synthesizer (`src/synthesizer/`):** Scalable dataset generator using `pandas` and `Faker` to scale raw IBM HR data to 100,000+ synthetic records with realistic SCD Type 2 employment histories.
2. **OLTP Schema (`sql/oltp/`):** Normalized database model designed for high-frequency write operations (employee onboarding, reviews, project updates).
3. **OLAP Schema (`sql/olap/`):** Star schema with `Dim_Employee` (SCD Type 2), `Dim_Department`, `Dim_Project`, `Dim_Date`, and `Fact_Performance_Reviews`.
4. **ETL Pipeline (`sql/etl/`):** SQL stored procedures utilizing CTEs and window functions for continuous incremental processing and SCD Type 2 merge logic.
5. **Python OOP DAL (`src/managers/` & `src/models/`):** Clean Data Access Layer with Singleton database connection pooling and manager classes.
6. **Streamlit App (`app/`):** Multi-page dashboard supporting operational data updates and executive analytical visualizations.
Run these SQL files in order using MySQL Workbench or the CLI:

```bash
# From MySQL CLI:
source sql/01_oltp_schema.sql
source sql/02_olap_schema.sql
source sql/03_etl_procedures.sql
```
sql/01_oltp_schema.sql
sql/02_olap_schema.sql
sql/03_etl_procedures.sql
```

---
**4. (Optional) Generate synthetic data**
### 4. (Optional) Generate and load synthetic data

## 📖 Planning Documentation
Drop the IBM HR CSV (`WA_Fn-UseC_-HR-Employee-Attrition.csv`) into the `dataset/` folder, then run:
If you want the warehouse pre-populated with 100k+ realistic employees:

For detailed technical blueprints, refer to [`Planning_docs/`](Planning_docs/):
1. Drop the IBM HR CSV (`WA_Fn-UseC_-HR-Employee-Attrition.csv`) into `dataset/`
2. Run the synthesizer:

```bash
python src/synthesizer/generate_data.py
```

- 📘 [00_MASTER_PLAN.md](Planning_docs/00_MASTER_PLAN.md) — Architectural overview & phase dependencies
- 📐 [01_FOLDER_STRUCTURE.md](Planning_docs/01_FOLDER_STRUCTURE.md) — Detailed layout & naming conventions
- 🧪 [02_DATA_SYNTHESIS.md](Planning_docs/02_DATA_SYNTHESIS.md) — Data scaling & SCD2 history generator
- 🗄️ [03_OLTP_DESIGN.md](Planning_docs/03_OLTP_DESIGN.md) — Relational schema & DDL specs
- 📊 [04_OLAP_DESIGN.md](Planning_docs/04_OLAP_DESIGN.md) — Dimensional modeling & SCD2 tracking
- ⚙️ [05_ETL_PIPELINE.md](Planning_docs/05_ETL_PIPELINE.md) — Stored procedures & data transformation logic
- 🐍 [06_PYTHON_ARCHITECTURE.md](Planning_docs/06_PYTHON_ARCHITECTURE.md) — Backend design & object models
- 🖥️ [07_STREAMLIT_APP.md](Planning_docs/07_STREAMLIT_APP.md) — UI design, forms, and chart specs
- 🌿 [08_GIT_AND_DEPLOYMENT.md](Planning_docs/08_GIT_AND_DEPLOYMENT.md) — Version control strategy & Streamlit Cloud deploy
This generates `dataset/staging_employees.csv` and `dataset/staging_employee_history.csv` — load them into the DB using the ETL procedure.
This writes `dataset/staging_employees.csv` and `dataset/staging_employee_history.csv`. Load them into `hr_oltp.staging_employees` and `hr_oltp.staging_employee_history`, then run the ETL procedures:

---
```sql
CALL sp_load_dim_date('2015-01-01', '2027-12-31');
CALL sp_load_dim_department();
CALL sp_load_dim_project();
CALL sp_load_dim_employee_scd2();
CALL sp_load_fact_performance_reviews();
```

## 🛠️ Contribution Guidelines
## Run the app
### 5. Run the app

We enforce feature branch naming (`F-xx-<name>`) and standardized commit messages (`vY.XX.ZZ-message`). Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for full branch and commit guidelines.
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## 📜 Code of Conduct
## Tech stack

Please review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing to ensure a collaborative environment.
- Python 3.10+
- Streamlit
- MySQL (mysql-connector-python)
- Pandas + Plotly
- Faker (for data synthesis)
| Layer | Tools |
|---|---|
| Language | Python 3.10+ |
| Web app | Streamlit |
| Database | MySQL (mysql-connector-python) |
| Data processing | pandas, Faker |
| Charts | Plotly Express |
| Config | python-dotenv |

---

## Diagrams

Detailed architecture diagrams live in [`diagrams/`](diagrams/):

| File | What it shows |
|---|---|
| [01_system_architecture.md](diagrams/01_system_architecture.md) | Full data pipeline from CSV to dashboard |
| [02_oltp_er_diagram.md](diagrams/02_oltp_er_diagram.md) | OLTP entity-relationship model |
| [03_olap_star_schema.md](diagrams/03_olap_star_schema.md) | OLAP star schema and foreign key layout |
| [04_scd2_flow.md](diagrams/04_scd2_flow.md) | How SCD Type 2 works step by step |
| [05_etl_pipeline.md](diagrams/05_etl_pipeline.md) | ETL stored procedure flow and run order |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming (`F-xx-<name>`) and commit message conventions (`vY.XX.ZZ-message`).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
