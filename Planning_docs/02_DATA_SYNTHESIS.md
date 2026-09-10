# Data Synthesis Strategy

## 1. Goal

Turn the ~1,470-row IBM HR Analytics dataset into a 100,000+ row dataset
that (a) looks statistically realistic, not duplicated, and (b) contains
built-in historical change records so the SCD Type 2 pipeline downstream
has real data to process.

This is two distinct problems — **scaling** and **history injection** —
and they should be two separate scripts/functions, not one tangled loop.

## 2. Step 1: Scaling to 100,000+ Rows

**Do not simply duplicate rows.** A grader/reviewer will notice repeated
`EmployeeNumber` or identical (Name, Salary, Age) combinations immediately.
Instead:

- Use the original 1,470 rows as a **statistical seed**, not literal source
  rows to copy.
- For each new synthetic employee:
  - Sample categorical fields (Department, JobRole, EducationField,
    Gender, MaritalStatus, Attrition) from the **empirical distribution**
    of the original dataset (`df['Department'].value_counts(normalize=True)`)
    rather than uniformly at random — this preserves realistic proportions
    (e.g. Sales should still be a large department).
  - Sample numeric fields (Age, MonthlyIncome, YearsAtCompany,
    DistanceFromHome) from a distribution fit to the original column
    (normal/lognormal, or simple bootstrap resampling with jitter), not
    a flat random range.
  - Use `Faker` for identity fields that shouldn't be real IBM sample
    data: `Faker().name()`, `Faker().email()`, synthetic `EmployeeID`.
  - Keep correlated fields consistent — e.g. `MonthlyIncome` should
    roughly track `JobLevel` and `TotalWorkingYears`, not be independently
    randomized, or the dataset will look nonsensical in dashboards later.

**Practical approach:**
```
1. Load original CSV with pandas.
2. Build per-column samplers:
   - categorical -> weighted random choice from value_counts()
   - numeric -> np.random.normal(mean, std) clipped to observed min/max,
     or bootstrap + small jitter
3. Loop / vectorize to generate N new rows (N = 100,000 - 1,470)
4. Concatenate original + synthetic rows
5. Assign sequential EmployeeID / surrogate-safe primary keys
6. Validate: check value_counts() and describe() on synthetic output
   roughly match the original's proportions
7. Export to data/synthesized/employees_100k.csv
```

Vectorize with `numpy`/`pandas` rather than row-by-row Python loops —
at 100k rows a naive `for` loop with `Faker` calls per field will be slow.
Pre-generate pools of Faker values (e.g. 10,000 names) and sample from
the pool with replacement if uniqueness isn't critical.

## 3. Step 2: Engineering SCD Type 2 History

The IBM dataset is a single snapshot — there's no "employee X was in
Department Y before moving to Z" story built in. You have to invent it.

**Approach:**

- Pick a subset of employees (e.g. 15–20% of the synthesized population)
  to have a history of 2+ records instead of just 1.
- For each selected employee, generate a **prior version** of their record
  dated ~2 years earlier, differing in one or more of:
  - `Department` (simulate a transfer)
  - `JobRole` / `JobLevel` (simulate a promotion)
  - `MonthlyIncome` (simulate a raise)
  - `Manager` (simulate a reporting line change)
- Assign each version:
  - `effective_start_date`
  - `effective_end_date` (the day before the next version starts; `NULL`
    or a far-future sentinel date for the current version)
  - `is_current` flag (`1` for the latest version, `0` for prior ones)
- Keep a **stable natural key** (`EmployeeID` or `EmployeeNumber`) across
  all versions of the same employee — this is what ties rows together
  before they get separate `surrogate_key` values in the warehouse.

**Output shape (conceptual):**

| EmployeeID (natural key) | Department | JobRole | MonthlyIncome | effective_start_date | effective_end_date | is_current |
|---|---|---|---|---|---|---|
| E10432 | Sales | Sales Rep | 4200 | 2024-01-01 | 2025-12-31 | 0 |
| E10432 | Sales | Senior Sales Rep | 5600 | 2026-01-01 | NULL | 1 |

This file becomes the input to both the OLTP load (only the *current*
row per employee, since OLTP reflects present state) and the OLAP ETL
(all rows, since the warehouse needs to preserve history).

## 4. Reproducibility

- Set a fixed `random.seed()` / `np.random.seed()` / `Faker.seed()` in
  `config.py` so the dataset is regenerable and diffable across runs.
- Log summary stats after generation (row count, % with history, column
  distributions) to a `data/synthesized/generation_report.txt` — useful
  both for debugging and as evidence for the "Data Synthesis & Scale"
  evaluation criterion.

## 5. Suggested Script Split (maps to `src/synthesizer/`)

- `config.py` — target row count, seed, history-subset percentage, date ranges.
- `scale_dataset.py` — loads IBM CSV, produces the 100k-row current-state table.
- `generate_history.py` — takes the scaled table, selects a subset, produces prior-version rows, outputs the combined historized CSV.
- Optionally `validate_synthetic.py` — sanity checks (distribution comparisons, null checks, referential sanity) before loading into MySQL.
