# OLAP Data Warehouse Design (Star Schema + SCD Type 2)

## 1. Purpose

The OLAP schema is read-optimized and answers analytical questions
("how did performance trend year over year", "who are top performers per
department") that would be slow or awkward against the normalized OLTP
schema. It is **denormalized on purpose** and stores **history**, unlike
OLTP.

## 2. Star Schema Layout

```
                     Dim_Date
                        │
   Dim_Employee ────  Fact_PerformanceReviews  ──── Dim_Department
   (SCD Type 2)           │
                     Dim_Project
```

### Fact_PerformanceReviews
```
├── review_fact_id (PK, surrogate)
├── employee_key (FK -> Dim_Employee.surrogate_key)
├── department_key (FK -> Dim_Department.surrogate_key)
├── project_key (FK -> Dim_Project.surrogate_key, nullable)
├── date_key (FK -> Dim_Date.surrogate_key)
├── performance_score
├── rating
└── review_natural_id   -- traceability back to OLTP Review.review_id
```

### Dim_Employee (SCD Type 2)
```
├── employee_key (PK, surrogate, auto-increment)
├── employee_natural_id       -- stable business key, e.g. OLTP employee_id
├── first_name, last_name
├── department_name           -- denormalized snapshot at that point in time
├── job_role
├── job_level
├── monthly_income
├── manager_name
├── effective_start_date
├── effective_end_date        -- NULL or 9999-12-31 sentinel for current row
└── is_current                -- 1 = current, 0 = historical
```

### Dim_Department / Dim_Project
```
├── department_key (PK, surrogate)
├── department_natural_id
├── department_name
└── location
```
(Dim_Project follows the same pattern with project fields.)

### Dim_Date
```
├── date_key (PK, surrogate, format YYYYMMDD as int)
├── full_date
├── day, month, quarter, year
├── month_name
└── is_weekend
```
Standard date dimension — generate once via a script/SQL loop covering
the full range your data spans (e.g. 2015–2026).

## 3. Why Surrogate Keys (not natural keys) as PKs

- Natural keys (`employee_id` from OLTP) can't uniquely identify a *row*
  once an employee has multiple historical versions in `Dim_Employee` —
  the same `employee_natural_id` will appear in 2+ rows.
- Surrogate keys (`employee_key`, auto-increment integers) give each
  historical version its own unique identity, and the Fact table points
  to the *specific version that was current at the time of the review* —
  this is the entire point of SCD Type 2 joins.

## 4. SCD Type 2 Mechanics (the core of this project)

When an employee's department/role/salary changes:

1. **Do not UPDATE the existing `Dim_Employee` row.**
2. Find the current row for that `employee_natural_id`
   (`WHERE employee_natural_id = X AND is_current = 1`).
3. Set that row's `effective_end_date = <change_date - 1 day>` and
   `is_current = 0`.
4. `INSERT` a new row with the new attribute values,
   `effective_start_date = <change_date>`, `effective_end_date = NULL`
   (or sentinel), `is_current = 1`.
5. New `employee_key` surrogate value is generated automatically for the
   new row (auto-increment).

**Fact table joins use whichever `employee_key` was current on the
`review_date`** — this is why a review submitted in 2024 correctly joins
to the "before promotion" dimension row, and a review submitted in 2026
joins to the "after promotion" row, even though both reviews are for the
same person.

## 5. Populating from the Synthesizer

The historized CSV from `02_DATA_SYNTHESIS.md` (with
`effective_start_date`, `effective_end_date`, `is_current` already
present) maps almost directly onto `Dim_Employee` — this is intentional,
so the synthesizer's job and the warehouse's schema are designed
together, not as two disconnected pieces.

## 6. Indexes & Performance (`sql/olap/03_indexes.sql`)

- Index `Dim_Employee(employee_natural_id, is_current)` — this is the
  lookup pattern used constantly during ETL and by the app's SCD2 update
  logic.
- Index `Fact_PerformanceReviews(employee_key)`,
  `Fact_PerformanceReviews(date_key)` for dashboard filter performance.
- Consider partitioning `Fact_PerformanceReviews` by year if row volume
  from 100k+ employees × multiple reviews gets large.

## 7. What to Show in the Dimensional Model Diagram

- All four dimension tables radiating from the fact table (classic star,
  not snowflake — don't further normalize `Dim_Department` out of
  `Dim_Employee`'s denormalized `department_name` field; that's expected
  redundancy in a star schema).
- Explicitly label surrogate keys vs. natural/business keys — graders will
  look for this distinction.
- Annotate `Dim_Employee` with a callout: "SCD Type 2 — see
  `effective_start_date` / `effective_end_date` / `is_current`."
