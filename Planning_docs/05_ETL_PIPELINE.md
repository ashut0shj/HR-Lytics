# ETL Pipeline: OLTP/Staging → OLAP

## 1. Purpose

Move data from staging/OLTP into the star schema, applying SCD Type 2
logic, using stored procedures with CTEs and window functions as required
by the assignment.

## 2. Pipeline Stages

```
staging.employees_raw  (100k+ synthesized rows, incl. history)
        │
        ▼
   sp_load_dim_department()   -- simplest, load first (Fact depends on it)
   sp_load_dim_project()
   sp_load_dim_date()          -- generate calendar range, independent of source data
        │
        ▼
   sp_load_dim_employee_scd2() -- the core procedure, see below
        │
        ▼
   sp_load_fact_performance_reviews()  -- depends on all dimensions existing first
```

Order matters: **dimensions must be loaded before the fact table**, since
the fact table's foreign keys need to resolve against existing surrogate
keys.

## 3. `sp_load_dim_employee_scd2` — Core Logic

Pseudocode (translate to MySQL stored procedure syntax):

```sql
CREATE PROCEDURE sp_load_dim_employee_scd2()
BEGIN
  -- Step 1: identify staging rows whose attributes differ from the
  -- current warehouse row (change detection)
  WITH changed_employees AS (
    SELECT s.employee_natural_id, s.department_name, s.job_role,
           s.monthly_income, s.effective_start_date
    FROM staging.employees_raw s
    JOIN warehouse.Dim_Employee d
      ON s.employee_natural_id = d.employee_natural_id
     AND d.is_current = 1
    WHERE s.department_name <> d.department_name
       OR s.job_role       <> d.job_role
       OR s.monthly_income <> d.monthly_income
  )

  -- Step 2: expire the old current row
  UPDATE warehouse.Dim_Employee d
  JOIN changed_employees c ON d.employee_natural_id = c.employee_natural_id
  SET d.is_current = 0,
      d.effective_end_date = DATE_SUB(c.effective_start_date, INTERVAL 1 DAY)
  WHERE d.is_current = 1;

  -- Step 3: insert the new current row
  INSERT INTO warehouse.Dim_Employee
    (employee_natural_id, department_name, job_role, monthly_income,
     effective_start_date, effective_end_date, is_current)
  SELECT employee_natural_id, department_name, job_role, monthly_income,
         effective_start_date, NULL, 1
  FROM changed_employees;

  -- Step 4: handle brand-new employees (no existing Dim_Employee row at all)
  INSERT INTO warehouse.Dim_Employee (...)
  SELECT ...
  FROM staging.employees_raw s
  LEFT JOIN warehouse.Dim_Employee d ON s.employee_natural_id = d.employee_natural_id
  WHERE d.employee_natural_id IS NULL;
END
```

This is the piece worth prototyping and testing in isolation (with a
small handful of test employees) before running it against the full
synthesized dataset — SCD2 bugs are easy to introduce and hard to spot
once buried in 100k rows.

## 4. Where Window Functions Belong

Window functions aren't part of the SCD2 mechanism itself — they belong
in the **transform/ranking logic**, e.g.:

- **Ranking employees within department by score**, used both in ETL
  (if pre-computing a rank column) and directly in dashboard queries:
  ```sql
  SELECT employee_key, department_key, performance_score,
         DENSE_RANK() OVER (
           PARTITION BY department_key ORDER BY performance_score DESC
         ) AS dept_rank
  FROM Fact_PerformanceReviews;
  ```
- **De-duplicating staging rows** before insert, if the synthesizer ever
  produces near-duplicate history rows for the same employee/date:
  ```sql
  WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY employee_natural_id, effective_start_date
      ORDER BY effective_start_date DESC
    ) AS rn
    FROM staging.employees_raw
  )
  SELECT * FROM ranked WHERE rn = 1;
  ```
- **Year-over-year deltas** for the dashboard (`LAG()`/`LEAD()` over
  `Dim_Date.year`, partitioned by employee or department).

## 5. Orchestration from Python (`src/etl/run_etl.py`)

Even though the transform logic lives in SQL stored procedures, Python
orchestrates the run:

```
1. Connect via db_manager (Singleton)
2. TRUNCATE or upsert staging table from the synthesized CSV (pandas .to_sql or LOAD DATA INFILE)
3. CALL sp_load_dim_department()
4. CALL sp_load_dim_project()
5. CALL sp_load_dim_date()
6. CALL sp_load_dim_employee_scd2()
7. CALL sp_load_fact_performance_reviews()
8. Log row counts before/after for a basic sanity check
```

Wrap each `CALL` in try/except with rollback on failure — partial ETL
runs (e.g. dimensions loaded but fact table failed) leave the warehouse
in a bad state, so consider wrapping the whole sequence in a transaction
where MySQL's engine allows it (note: DDL/some DCL statements auto-commit
in MySQL, so test this carefully).

## 6. Also Needed by the App (not just batch ETL)

The Streamlit "update employee department" form (Phase 4 requirement)
needs to trigger this **same SCD2 logic on a single employee**, not just
the batch job. Two options:

- Call `sp_load_dim_employee_scd2()` scoped to one employee (pass
  `employee_natural_id` as a parameter, add a `WHERE` filter).
- Or replicate the expire-then-insert logic directly in Python inside
  `EmployeeManager.update_department()`.

Prefer the stored-procedure route for consistency — one source of truth
for SCD2 logic, called both by batch ETL and by the live app.
