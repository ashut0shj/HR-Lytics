# Enterprise Employee Analytics & Data Warehouse — Master Plan

## 1. Purpose

This document is the entry point for the project. It describes the overall
flow, how the pieces connect, and links out to the detailed planning docs
for each subsystem. Read this first, then dive into the component doc you
need.

## 2. System Flow (High Level)

```
                    ┌─────────────────────────┐
                    │   IBM HR Analytics CSV   │   (~1,470 rows, source dataset)
                    └────────────┬─────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   Data Synthesizer (Python)    │
                 │  pandas + Faker                │
                 │  - scale to 100,000+ rows      │
                 │  - inject SCD Type 2 history    │
                 └────────────┬───────────────────┘
                                 │  synthesized_employees.csv
                                 ▼
                 ┌───────────────────────────────┐
                 │   MySQL: staging schema        │
                 │   (raw load, minimal cleaning) │
                 └────────────┬───────────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   MySQL: OLTP schema           │
                 │   (normalized operational DB)  │
                 └────────────┬───────────────────┘
                                 │  ETL (Stored Procedures / CTEs / Window Fns)
                                 ▼
                 ┌───────────────────────────────┐
                 │   MySQL: OLAP schema           │
                 │   (Star Schema, SCD Type 2)    │
                 └────────────┬───────────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   Python OOP Data Access Layer │
                 │   db_manager / entities /      │
                 │   managers                     │
                 └────────────┬───────────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   Streamlit App                │
                 │   - Data entry (writes OLTP)   │
                 │   - Dashboards (reads OLAP)    │
                 └────────────┬───────────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   Streamlit Community Cloud    │
                 │   (public deployment)          │
                 └───────────────────────────────┘
```

**Key principle:** OLTP is the system of record for day-to-day writes
(onboarding, project assignment, reviews). OLAP is a read-optimized,
historized copy used only for analytics. They are never queried
interchangeably by the app — writes go to OLTP, dashboards read from OLAP.

## 3. Phase-to-Deliverable Map

| Phase | What you build | Detailed doc |
|---|---|---|
| 1a | Data synthesizer (scale + SCD2 history injection) | `02_DATA_SYNTHESIS.md` |
| 1b | OLTP ER model + DDL | `03_OLTP_DESIGN.md` |
| 1c | OLAP star schema + SCD2 design | `04_OLAP_DESIGN.md` |
| 2 | ETL: stored procedures, CTEs, window functions | `05_ETL_PIPELINE.md` |
| 3 | Python OOP backend (Singleton DB, entities, managers) | `06_PYTHON_ARCHITECTURE.md` |
| 4 | Streamlit UI: data entry + dashboards | `07_STREAMLIT_APP.md` |
| 5 | Git workflow + Streamlit Cloud deployment | `08_GIT_AND_DEPLOYMENT.md` |

Folder/repo layout lives in `01_FOLDER_STRUCTURE.md`.

## 4. Suggested Build Order

Don't build strictly phase-by-phase — some things need to exist before
others regardless of "phase number":

1. **Repo scaffold** (`01_FOLDER_STRUCTURE.md`) — empty folders, README stubs, `.gitignore`, `requirements.txt`.
2. **OLTP DDL** — you need tables before you have anywhere to load data.
3. **Data synthesizer** — generates the CSVs that will populate OLTP.
4. **Load into staging → OLTP.**
5. **OLAP DDL** (star schema) — design against the *shape* of OLTP data.
6. **ETL stored procedures** — OLTP → OLAP, including SCD2 merge logic.
7. **Python OOP layer** — build against a populated database, not an empty one, so you can test real queries.
8. **Streamlit app** — data entry pages first (simpler), dashboards second (depend on OLAP being populated).
9. **Git hygiene + deployment** — should be continuous from day one (commits/branches), but the Cloud deploy step is last.

## 5. Cross-Cutting Concerns

- **SCD Type 2** is the throughline: it must be reflected in (a) synthesized
  historical records, (b) `Dim_Employee` schema, (c) ETL merge logic, and
  (d) the Streamlit "update employee" form. Treat it as one feature
  implemented in four places, not four separate features.
- **Volume (100k+ rows):** test query performance early with `EXPLAIN`,
  add indexes on FK/surrogate key columns, avoid `SELECT *` in dashboard
  queries.
- **Documentation as you go:** update `README.md` and the architecture doc
  after each phase, not at the end — details are forgotten quickly.

## 6. Documents in This Plan

- `01_FOLDER_STRUCTURE.md` — repo layout, naming conventions
- `02_DATA_SYNTHESIS.md` — Faker/pandas scaling strategy, SCD2 seeding
- `03_OLTP_DESIGN.md` — ER model, normalization notes, DDL outline
- `04_OLAP_DESIGN.md` — star schema, surrogate keys, SCD2 mechanics
- `05_ETL_PIPELINE.md` — stored procedures, CTEs, window functions
- `06_PYTHON_ARCHITECTURE.md` — OOP class design (Singleton, entities, DAL)
- `07_STREAMLIT_APP.md` — page structure, forms, dashboard queries
- `08_GIT_AND_DEPLOYMENT.md` — branching model, PR flow, Cloud deploy steps
