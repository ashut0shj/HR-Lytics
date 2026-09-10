# Folder Structure & Repo Conventions

## 1. Top-Level Layout

```
employee-analytics-warehouse/
├── README.md                     # project overview, setup instructions
├── requirements.txt               # pinned Python dependencies
├── .gitignore
├── .env.example                   # template for DB credentials (never commit real .env)
├── .streamlit/
│   └── config.toml                # theme, page config for Streamlit
│
├── data/
│   ├── raw/
│   │   └── ibm_hr_attrition.csv   # original ~1,470 row dataset (source)
│   ├── synthesized/
│   │   └── employees_100k.csv     # output of the synthesizer script
│   └── README.md                  # data dictionary / column notes
│
├── diagrams/
│   ├── er_diagram_oltp.drawio     # editable ER diagram (Draw.io/Lucidchart export)
│   ├── er_diagram_oltp.png
│   ├── dimensional_model_olap.drawio
│   └── dimensional_model_olap.png
│
├── sql/
│   ├── oltp/
│   │   ├── 01_ddl_tables.sql
│   │   ├── 02_constraints_indexes.sql
│   │   └── 03_sample_dml.sql
│   ├── olap/
│   │   ├── 01_ddl_dimensions.sql
│   │   ├── 02_ddl_fact.sql
│   │   └── 03_indexes.sql
│   ├── etl/
│   │   ├── sp_load_dim_employee_scd2.sql
│   │   ├── sp_load_dim_department.sql
│   │   ├── sp_load_dim_project.sql
│   │   ├── sp_load_dim_date.sql
│   │   └── sp_load_fact_performance_reviews.sql
│   └── analytics/
│       ├── yoy_performance_trends.sql
│       ├── top_performers_dense_rank.sql
│       └── attrition_risk.sql
│
├── src/
│   ├── synthesizer/
│   │   ├── __init__.py
│   │   ├── scale_dataset.py       # pandas+Faker row scaling
│   │   ├── generate_history.py    # SCD2 historical record injection
│   │   └── config.py              # constants: target row count, seed, etc.
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── db_manager.py          # Singleton DatabaseConnection class
│   │
│   ├── models/                    # entity classes
│   │   ├── __init__.py
│   │   ├── employee.py
│   │   ├── project.py
│   │   └── review.py
│   │
│   ├── managers/                  # Data Access Layer (DAL)
│   │   ├── __init__.py
│   │   ├── employee_manager.py
│   │   ├── project_manager.py
│   │   ├── review_manager.py
│   │   └── analytics_manager.py
│   │
│   └── etl/
│       ├── __init__.py
│       ├── run_etl.py             # orchestrates calling stored procedures
│       └── scd2_helpers.py        # Python-side SCD2 utility functions if needed
│
├── app/
│   ├── Home.py                    # Streamlit entry point
│   └── pages/
│       ├── 1_Onboard_Employee.py
│       ├── 2_Manage_Projects.py
│       ├── 3_Submit_Review.py
│       ├── 4_Dashboard_Performance.py
│       ├── 5_Dashboard_Attrition.py
│       └── 6_Dashboard_Projects.py
│
├── tests/
│   ├── test_synthesizer.py
│   ├── test_managers.py
│   └── test_scd2_logic.py
│
└── docs/
    ├── ARCHITECTURE.md            # mirrors the Google Doc, kept in-repo
    ├── SETUP.md                   # local dev + MySQL setup steps
    └── DATA_WAREHOUSE_LOGIC.md    # SCD2 explanation, star schema rationale
```

## 2. Naming Conventions

- **SQL files:** numbered prefixes (`01_`, `02_`) inside each folder to
  enforce execution order.
- **Streamlit pages:** numeric prefix controls sidebar order automatically.
- **Python modules:** `snake_case.py`; classes inside are `PascalCase`.
- **Stored procedures:** prefix `sp_` + `load_` or `sync_` + target table name.
- **Branches:** `feature/<short-description>` (e.g. `feature/database-design`,
  `feature/streamlit-dashboard`, `feature/scd2-etl`).

## 3. Why This Layout

- `sql/oltp`, `sql/olap`, `sql/etl` are separated so graders (and you) can
  tell at a glance which layer a script belongs to — this maps directly
  onto the evaluation criteria (Data Warehousing, SQL Mastery are scored
  separately from Python Architecture).
- `src/` vs `app/` split keeps business logic (DB access, models) testable
  independent of Streamlit — you can unit test `managers/` without spinning
  up the UI.
- `data/raw` vs `data/synthesized` makes it obvious what's the untouched
  source vs. generated output, and lets `.gitignore` exclude the large
  100k-row file from version control if needed (see below).

## 4. .gitignore Essentials

```
.env
__pycache__/
*.pyc
.streamlit/secrets.toml
data/synthesized/*.csv     # optional: regenerate via script instead of committing 100k+ rows
venv/
.DS_Store
```

If the assignment requires the synthesized dataset to be *in* the repo,
remove that line — but consider committing a compressed `.csv.gz` instead
of raw CSV given the row count.
