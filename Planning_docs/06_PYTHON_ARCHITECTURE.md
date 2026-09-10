# Python Application Architecture (OOP)

## 1. Layering

```
app/ (Streamlit pages)
   │  calls
   ▼
src/managers/  (DAL — business logic + CRUD orchestration)
   │  uses
   ▼
src/models/  (entity classes — plain data + behavior, no DB code)
   │  persisted via
   ▼
src/db/db_manager.py  (Singleton connection)
   │
   ▼
MySQL (OLTP + OLAP)
```

Streamlit pages should never write raw SQL directly — they call manager
methods. This keeps the UI layer thin and makes the DAL testable without
Streamlit running.

## 2. `db_manager.py` — Singleton Connection

```python
import mysql.connector
from mysql.connector import pooling

class DatabaseConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_pool(*args, **kwargs)
        return cls._instance

    def _init_pool(self, host, user, password, database, pool_size=5):
        self._pool = pooling.MySQLConnectionPool(
            pool_name="app_pool",
            pool_size=pool_size,
            host=host, user=user, password=password, database=database,
        )

    def get_connection(self):
        return self._pool.get_connection()
```

Notes:
- Using a **connection pool** inside the Singleton (rather than one raw
  connection) is safer for Streamlit, which can re-run scripts on every
  interaction — a single shared connection object gets fragile under
  reruns/threading, a pool handles it more gracefully.
- Load credentials from environment variables / `.streamlit/secrets.toml`,
  never hardcode.

## 3. Entity Classes (`src/models/`)

Plain objects representing a row — hold attributes and simple derived
behavior, but **no SQL**.

```python
class Employee:
    def __init__(self, employee_id, first_name, last_name, department_id,
                 job_role, monthly_income, manager_id=None):
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.department_id = department_id
        self.job_role = job_role
        self.monthly_income = monthly_income
        self.manager_id = manager_id

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def give_raise(self, percent):
        self.monthly_income *= (1 + percent / 100)
```

`Project` and `Review` follow the same pattern: constructor + a couple of
domain methods (e.g. `Review.is_high_performer()` returning
`self.performance_score >= 4`).

## 4. Manager Classes (`src/managers/`) — DAL

Managers inherit shared DB access behavior and implement CRUD + business
operations. Consider a small base class to avoid repeating
connection/error-handling boilerplate:

```python
class BaseManager:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def _execute(self, query, params=None, fetch=False):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"DB operation failed: {e}") from e
        finally:
            cursor.close()
            conn.close()


class EmployeeManager(BaseManager):
    def create_employee(self, employee: Employee):
        query = """INSERT INTO Employee
                    (first_name, last_name, department_id, job_role, monthly_income)
                    VALUES (%s, %s, %s, %s, %s)"""
        self._execute(query, (employee.first_name, employee.last_name,
                               employee.department_id, employee.job_role,
                               employee.monthly_income))

    def update_department(self, employee_id, new_department_id, change_date):
        # This is the SCD2 trigger point described in 05_ETL_PIPELINE.md
        query = "CALL sp_load_dim_employee_scd2_single(%s, %s, %s)"
        self._execute(query, (employee_id, new_department_id, change_date))

    def get_employee(self, employee_id) -> Employee:
        rows = self._execute("SELECT * FROM Employee WHERE employee_id = %s",
                              (employee_id,), fetch=True)
        return Employee(**rows[0]) if rows else None


class AnalyticsManager(BaseManager):
    def top_performers_by_department(self):
        query = """
            SELECT employee_key, department_key, performance_score,
                   DENSE_RANK() OVER (
                     PARTITION BY department_key ORDER BY performance_score DESC
                   ) AS dept_rank
            FROM Fact_PerformanceReviews
        """
        return self._execute(query, fetch=True)
```

## 5. Error Handling Pattern

- Every DB-touching method goes through `_execute()` (or equivalent),
  centralizing try/except/rollback so individual manager methods stay
  readable.
- Raise domain-specific exceptions where it helps the UI layer show a
  useful message (e.g. `EmployeeNotFoundError`), rather than letting raw
  `mysql.connector` exceptions bubble to Streamlit.
- Streamlit pages wrap manager calls in their own try/except purely for
  UI feedback (`st.error(...)`), not for retry logic.

## 6. Class Responsibility Summary

| Class | Responsibility | Does NOT do |
|---|---|---|
| `DatabaseConnection` | Own the connection pool (Singleton) | Business logic |
| `Employee`, `Project`, `Review` | Hold data + simple domain behavior | SQL |
| `BaseManager` | Shared query execution + error handling | Domain-specific queries |
| `EmployeeManager`, `ProjectManager`, `ReviewManager` | CRUD for their entity | Analytics/aggregation |
| `AnalyticsManager` | Read-only OLAP queries for dashboards | Writes |
