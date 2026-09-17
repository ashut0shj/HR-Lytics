# HR-Lytics

HR-Lytics is a small HR analytics platform. It has two databases — one for daily operations (OLTP) and one for reporting/analytics (OLAP) — plus a Streamlit dashboard on top.

* **OLTP (`hr_oltp`)**: where day-to-day writes happen — onboarding an employee, creating a project, assigning people to it, submitting a review.
* **OLAP (`hr_olap`)**: a read-only, history-aware copy of the important parts of OLTP, used only for the analytics dashboard. It keeps old versions of an employee's record around (SCD Type 2) so you can see how someone's department/role/salary changed over time.

Data always flows OLTP → OLAP through the migration/ETL step described below — the app never writes to OLAP directly (except one small SCD2 helper for department changes).

---

## Project Structure

```text
HR-Lytics/
├── migrate.py                  # Run this to set up / refresh both databases
├── app.py                      # Streamlit app (dashboard + data entry)
├── requirements.txt
├── .env.example                # Copy this to .env and fill in your DB details
├── src/
│   ├── db/
│   │   ├── db_wrapper.py       # Handles the MySQL connection
│   │   └── query_loader.py     # Loads named SQL snippets from the sql/ files
│   ├── managers/
│   │   └── managers.py         # All the business logic (create employee, run ETL, etc.)
│   ├── models/
│   │   └── models.py           # Employee / Project / Review data classes
│   └── synthesizer/
│       └── generate_data.py    # Turns the small sample CSV into ~1,000,000 rows
├── sql/
│   ├── 01_oltp_schema.sql      # Creates hr_oltp tables
│   ├── 02_olap_schema.sql      # Creates hr_olap tables
│   ├── 03_etl_procedures.sql   # Stored procedures that move data OLTP → OLAP
│   ├── 04_analytics_queries.sql
│   ├── oltp/                   # SQL used by the OLTP managers
│   └── olap/                   # SQL used by the analytics dashboard
├── diagrams/                   # Architecture & schema diagrams
└── dataset/                    # Source CSV + generated data (not committed)
```

---

## Setup

**Prerequisites:** Python 3.10+, a MySQL server (this project was built and deployed against Aiven's managed MySQL), pip.

```bash
git clone <repo-url>
cd HR-Lytics
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your database details:

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

## Running it the first time

Everything is driven by one script, `migrate.py`, run from the project root:

```bash
python migrate.py
```

This does the following, in order, every time you run it:

1. **Generate data** — if `dataset/staging_employees.csv` doesn't exist yet, it runs `src/synthesizer/generate_data.py`, which takes the small sample CSV (`WA_Fn-UseC_-HR-Employee-Attrition.csv`) and scales it up to about 1,000,000 realistic employee rows, with some of them given a fake history (an old department/role/salary) so SCD2 has something to show.
2. **Build the schemas** — runs `sql/01_oltp_schema.sql`, `sql/02_olap_schema.sql`, then `sql/03_etl_procedures.sql`, so both `hr_oltp` and `hr_olap` get created (or updated) and all the stored procedures are (re)installed.
3. **Load OLTP** — loads the generated CSVs into the staging tables, then fills `departments` and `employees` from staging.
4. **Run the ETL into OLAP** — calls the stored procedures in this order:
   - `sp_load_dim_date`
   - `sp_load_dim_department`
   - `sp_load_dim_project`
   - `sp_load_dim_employee_scd2`
   - `sp_load_dim_employee_incremental`
   - `sp_load_fact_performance_reviews`
   - `sp_load_fact_reviews_incremental`
5. **Verify** — prints a row count for every important table in both databases so you can see at a glance that nothing came out empty.

Once it finishes, start the app:

```bash
streamlit run app.py
```

## Running it again later (keeping it up to date)

You don't need to re-run `migrate.py` for everyday use — it's meant for first-time setup or a full rebuild. Once the app is running, any employee you onboard, department change you make, or review you submit goes straight into `hr_oltp`. To get those changes reflected in the analytics dashboard, use the **"Refresh OLAP"** button at the top of the app. It re-runs the OLAP procedures listed above (minus the one-time dimension loads), so newly onboarded employees and newly submitted reviews show up in the dashboard without needing a full migration.

If you want to rebuild everything from scratch (fresh synthetic data, clean tables), delete the two CSVs in `dataset/` and run `python migrate.py` again.

---

## Using the App

* **Analytics Dashboard** — headcount by department, attrition rate, salary by role, performance trends, top performers, and SCD2 history — all read from `hr_olap`.
* **Onboard Employee** — add a new employee, or move an existing one to a different department (this triggers an SCD2 change immediately, no refresh needed).
* **Projects & Assignments** — create a project and assign employees to it.
* **Submit Review** — record a performance review for an employee. Needs an OLAP refresh to show up on the dashboard.
* **Data Explorer** — browse and filter any OLTP table directly.

---

## Tech Stack

* **Frontend**: Streamlit, Plotly
* **Backend**: Python
* **Database**: MySQL (`mysql-connector-python`), hosted on Aiven
* **Data**: Pandas, Faker
* **Config**: python-dotenv
