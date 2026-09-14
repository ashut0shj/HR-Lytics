# ETL Pipeline

The ETL (Extract, Transform, Load) pipeline moves data from the raw staging tables into the clean OLAP star schema. It runs as a set of MySQL stored procedures defined in `sql/03_etl_procedures.sql`.

## Overview

```mermaid
flowchart LR
    subgraph Source ["Source (hr_oltp)"]
        SE["staging_employees"]
        SH["staging_employee_history"]
        OD["departments"]
        OP["projects"]
    end

    subgraph ETL ["ETL Stored Procedures"]
        P1["sp_load_dim_date\nPre-populate 2015–2027\ndates once"]
        P2["sp_load_dim_department\nInsert missing departments\nfrom hr_oltp.departments"]
        P3["sp_load_dim_project\nInsert missing projects\nfrom hr_oltp.projects"]
        P4["sp_load_dim_employee_scd2\nStep 1: load history rows (is_current=0)\nStep 2: close changed current rows\nStep 3: insert new current rows"]
        P5["sp_load_fact_performance_reviews\nOne fact row per staged employee\njoined to current employee_key"]
    end

    subgraph Target ["Target (hr_olap)"]
        DD["Dim_Date"]
        DDept["Dim_Department"]
        DP["Dim_Project"]
        DE["Dim_Employee"]
        FP["Fact_PerformanceReviews"]
    end

    OD --> P2
    OP --> P3
    SE --> P4
    SH --> P4
    SE --> P5

    P1 --> DD
    P2 --> DDept
    P3 --> DP
    P4 --> DE
    P5 --> FP
```

## Run order

The procedures must be called in this exact sequence — each one depends on the previous:

```sql
CALL sp_load_dim_date('2015-01-01', '2027-12-31');
CALL sp_load_dim_department();
CALL sp_load_dim_project();
CALL sp_load_dim_employee_scd2();
CALL sp_load_fact_performance_reviews();
```

## Design notes

- **Idempotent** — all procedures use `WHERE NOT EXISTS` guards or UPDATE+INSERT patterns, so re-running them won't create duplicates.
- **Cross-database joins** — the procedures reference both `hr_oltp.*` and `hr_olap.*` tables directly. Both schemas must live on the same MySQL server.
- **SCD2 merge logic** — `sp_load_dim_employee_scd2` is the most complex: it detects attribute changes by comparing incoming staging rows against existing `Dim_Employee` rows, closes stale versions, and opens new ones.

