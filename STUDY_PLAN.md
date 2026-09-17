# Study Plan — HR-Lytics

Not part of the submission, just notes for us to study the codebase before we present it. Read `README.md` first for the overall setup and run order, then use your section below.

---

## Ashutosh & Nathan — Backend, Classes, DB Connectivity

Focus: `src/db/db_wrapper.py`, `src/db/query_loader.py`, `src/models/models.py`, `migrate.py`

1. **`db_wrapper.py`** — this is the only place that talks to MySQL. Understand:
   - `connect()` and `get_connection()` — how it reconnects if the connection drops.
   - `execute_query` / `execute_many` (writes) vs `fetch_all` / `fetch_one` / `query_df` (reads).
   - Why `autocommit=True` is set, and what that means for writes not needing manual commits.
   - `call_procedure()` — how it calls a stored procedure and drains leftover result sets with `nextset()`.

2. **`query_loader.py`** — small file, but know it cold. `load_named()` reads a `.sql` file and splits it into named blocks using `-- comment` lines as headers. Be able to explain why SQL lives in `.sql` files instead of Python strings.

3. **`models.py`** — `Employee`, `Project`, `Review` are plain dataclasses, no DB logic in them. Know the difference between a model (just data) and a manager (data + DB operations).

4. **`migrate.py`** — the one script that sets everything up. Walk through it top to bottom: generate data → build schemas → load OLTP → run ETL → verify. Be ready to explain what happens if you run it a second time (it's safe to re-run).

5. Be able to answer: *"If I add a new employee in the app, which file/function actually inserts the row, and how does it get a database connection?"* (Answer path: `app.py` → `EmployeeManager.create()` → `BaseManager.db` → `DBWrapper.execute_query()`.)

---

## Shadan — SQL (Schemas + ETL)

Focus: everything in `sql/`

1. **`01_oltp_schema.sql`** and **`02_olap_schema.sql`** — know every table, its columns, and its foreign keys. Be able to draw the OLTP tables (departments, employees, projects, assignments, reviews, staging tables) and the OLAP star schema (Dim_Employee, Dim_Department, Dim_Project, Dim_Date, Fact_PerformanceReviews) from memory.

2. **`03_etl_procedures.sql`** — this is the core of the project. Know what each procedure does and the order they run in:
   - `sp_load_dim_date` — fills the date dimension for a date range.
   - `sp_load_dim_department` / `sp_load_dim_project` — copy dimension data from OLTP.
   - `sp_load_dim_employee_scd2` — the SCD Type 2 logic: closes out an employee's old row (`is_current = 0`, sets `end_date`) when something changed, and opens a new current row.
   - `sp_load_dim_employee_incremental` — catches employees added straight into `hr_oltp.employees` (via the app) that never went through the CSV staging load.
   - `sp_load_fact_performance_reviews` — loads the one-time bulk review snapshot from `staging_employees`.
   - `sp_load_fact_reviews_incremental` — loads real reviews submitted through the app's `reviews` table.

3. **`04_analytics_queries.sql`** and **`sql/olap/analytics.sql`** — these power the dashboard. Be able to explain the window function used for "Top Performers by Department" (`RANK() OVER (PARTITION BY department_name ORDER BY avg_performance_rating DESC)`).

4. Be ready to explain SCD Type 2 in plain words: we never overwrite an employee's history, we close the old row and add a new one, so you can always ask "what was true on this date."

---

## Shreyashi — Streamlit App, Data Cleaning/Management, Analytics

Focus: `app.py`, `src/managers/managers.py`, `src/synthesizer/generate_data.py`

1. **`generate_data.py`** — this is the data cleaning/scaling step. Understand:
   - It starts from a small real dataset (~1,470 rows) and clones/samples it up to ~1,000,000 rows.
   - It fakes new names, emails, and hire dates per row (using Faker) so cloned rows don't look identical.
   - `build_scd2_tables()` — for a fraction of employees, it manufactures an "old" version of their record (older department/role/lower salary) and puts it in the history CSV, so SCD2 has something real to show once loaded.

2. **`managers.py`** — one manager class per feature area:
   - `EmployeeManager`, `DepartmentManager`, `ProjectManager`, `ReviewManager` — OLTP reads/writes.
   - `AnalyticsManager` — every dashboard chart is one method here (`headcount_by_department`, `attrition_overview`, `year_over_year_trend`, `top_performers_by_department`, `salary_by_job_role`, `scd2_change_history`), plus `refresh_olap()` which re-runs the ETL procedures on demand, and `apply_scd2_department_change()` for instant department-change history.
   - `ExplorerManager` — powers the free-form table browser.
   - Know the pattern: every manager extends `BaseManager`, which just holds a `DBWrapper` and wraps queries in try/except so one bad query doesn't crash the app.

3. **`app.py`** — the Streamlit UI. Walk through each page (`Analytics Dashboard`, `Onboard Employee`, `Projects & Assignments`, `Submit Review`, `Data Explorer`) and match each button/form to the manager method it calls. Also understand the "Refresh OLAP" button at the top — why it exists (new employees/reviews only reach the dashboard after this is pressed) and what it calls under the hood.

4. Be ready to explain, end to end: *"I submit a review in the app — what has to happen before it shows up on the Year-over-Year Performance Trend chart?"* (Answer: review is inserted into `hr_oltp.reviews` → user clicks Refresh OLAP → `sp_load_fact_reviews_incremental` runs → chart re-queries `hr_olap` and includes it.)
