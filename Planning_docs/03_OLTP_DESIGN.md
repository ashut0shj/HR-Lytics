# OLTP Database Design (Operational / Relational)

## 1. Purpose

The OLTP schema backs the live application — it's what the Streamlit forms
read from and write to when someone onboards an employee, assigns a
project, or submits a review. It should be **normalized** (3NF) to avoid
update anomalies, since it's write-heavy and reflects *current* state only
(no history — that's the warehouse's job).

## 2. Core Entities

- **Employee** — one row per current employee.
- **Department** — lookup table.
- **Project** — one row per project.
- **Assignment** — junction table: which employees are on which projects (many-to-many).
- **Review** — performance review events, tied to an employee.
- **Manager relationship** — self-referencing FK on Employee (`manager_id`) or a separate table if reporting lines need their own history.

## 3. Suggested ER Structure

```
Department
├── department_id (PK)
├── department_name
└── location

Employee
├── employee_id (PK)
├── first_name, last_name, email
├── department_id (FK -> Department)
├── manager_id (FK -> Employee, nullable, self-reference)
├── job_role
├── job_level
├── monthly_income
├── hire_date
└── is_active

Project
├── project_id (PK)
├── project_name
├── department_id (FK -> Department)
├── start_date
└── end_date

Assignment
├── assignment_id (PK)
├── employee_id (FK -> Employee)
├── project_id (FK -> Project)
├── role_on_project
└── assigned_date

Review
├── review_id (PK)
├── employee_id (FK -> Employee)
├── review_date
├── performance_score
├── rating
└── comments
```

## 4. Normalization Notes

- **Department** is separated out so department name/location changes
  don't require touching every employee row.
- **Assignment** exists because Employee↔Project is many-to-many — an
  employee can be on multiple projects, and a project has multiple
  employees. Don't try to embed a project list directly on Employee.
- **Review** is one-to-many from Employee — an employee accumulates
  multiple reviews over time. This table is itself naturally "historical"
  even without SCD2, since each review is an immutable event row.
- Keep **Employee** representing *only current state* — no
  `is_current`/`effective_date` columns here; that complexity belongs
  in the OLAP `Dim_Employee`, not OLTP. When a department/role/salary
  changes, OLTP does an `UPDATE` in place; it's the ETL's job to notice
  the change and version it in the warehouse.

## 5. DDL Checklist (`sql/oltp/01_ddl_tables.sql`)

- Explicit `PRIMARY KEY` on every table.
- `FOREIGN KEY` constraints with `ON DELETE`/`ON UPDATE` behavior decided
  deliberately (e.g. `ON DELETE RESTRICT` for Employee→Department so you
  can't orphan employees by deleting a department).
- `NOT NULL` on required business fields (email, hire_date, department_id).
- `UNIQUE` constraint on Employee.email.
- Sensible `CHECK` constraints where MySQL version supports them (e.g.
  `performance_score BETWEEN 1 AND 5`).

## 6. Indexes (`sql/oltp/02_constraints_indexes.sql`)

- Index FK columns (`employee_id`, `department_id`, `project_id`) — MySQL
  auto-indexes some FK columns but confirm explicitly.
- Composite index on `Assignment(employee_id, project_id)` for fast
  membership lookups.
- Index `Review(employee_id, review_date)` for "latest review per
  employee" queries.

## 7. What Loads Here from the Synthesizer

Only the **current-state row** per employee (`is_current = 1` from the
synthesized dataset) gets loaded into OLTP `Employee`. The historical
prior-version rows are *not* loaded into OLTP — they exist purely to feed
the OLAP SCD2 pipeline. This is a good thing to state explicitly in your
architecture doc, since it's a common point of confusion.
