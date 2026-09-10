# Streamlit Application Design

## 1. Page Structure

Using Streamlit's multipage convention (`app/pages/`, numeric prefixes
control sidebar order):

```
app/
├── Home.py                        # landing page, high-level KPIs
└── pages/
    ├── 1_Onboard_Employee.py      # OLTP write
    ├── 2_Manage_Projects.py       # OLTP write
    ├── 3_Submit_Review.py         # OLTP write
    ├── 4_Dashboard_Performance.py # OLAP read
    ├── 5_Dashboard_Attrition.py   # OLAP read
    └── 6_Dashboard_Projects.py    # OLAP read
```

Split clearly: pages 1–3 are **write** pages hitting OLTP through
Managers; pages 4–6 are **read-only** dashboards hitting OLAP through
`AnalyticsManager`. Never mix the two in one page — it blurs the OLTP/OLAP
separation that's central to this project's grading criteria.

## 2. Data Entry Pages (OLTP)

### `1_Onboard_Employee.py`
- Form fields: name, email, department (selectbox populated from
  `Department` table), job role, monthly income, manager (searchable
  selectbox from existing employees).
- On submit: `EmployeeManager.create_employee(...)`, show `st.success`.
- Validate before submit (required fields, email format, income > 0).

### `2_Manage_Projects.py`
- Two sub-sections: create a project, and assign employees to an existing
  project (multiselect of employees → `AssignmentManager` or extend
  `ProjectManager`).

### `3_Submit_Review.py`
- Select employee → form for score/rating/comments → `ReviewManager.create_review(...)`.
- This is what eventually feeds `Fact_PerformanceReviews` via ETL.

### Department change → SCD2 trigger
Wherever the UI allows changing an employee's department/role/salary
(likely a section of the Onboard/Manage page, or a dedicated "Update
Employee" page), the submit action must call
`EmployeeManager.update_department(...)`, which internally invokes the
SCD2 stored procedure — **not** a plain `UPDATE`. Label this clearly in
the UI copy (e.g. a caption: "This change will be tracked historically in
the data warehouse") since it's a distinguishing feature of the app worth
surfacing to the user, not hiding.

## 3. Dashboard Pages (OLAP)

### `4_Dashboard_Performance.py` — Year-over-Year Trends
- Filter widgets: department (multiselect), year range (slider).
- Query via `AnalyticsManager` joining `Fact_PerformanceReviews` →
  `Dim_Date` → `Dim_Employee`/`Dim_Department`.
- Chart: line chart (Plotly `px.line`) of average performance score by
  year, optionally faceted by department.

### `5_Dashboard_Attrition.py` — Attrition Risk
- Uses OLAP data (and possibly OLTP `is_active` flag) to surface risk
  indicators: e.g. employees with declining scores, long tenure without
  promotion, below-median income for their role.
- Present as a ranked table + bar chart of risk by department.

### `6_Dashboard_Projects.py` — Top Performers / Bottlenecks
- Uses `DENSE_RANK() OVER (PARTITION BY department ...)` query from
  `AnalyticsManager.top_performers_by_department()`.
- Show as a table with rank column, or a bar chart top-N per department.
- Project bottleneck view: count of active assignments per project vs.
  project team size/target, flagging over-allocated projects.

## 4. Caching

Wrap `AnalyticsManager` read methods with `@st.cache_data(ttl=...)` where
the query is expensive and doesn't need to be real-time — dashboards over
100k+ fact rows benefit significantly. Don't cache the write-path manager
calls.

```python
@st.cache_data(ttl=300)
def load_top_performers():
    return AnalyticsManager(db).top_performers_by_department()
```

## 5. Secrets & Connection in Streamlit

Store DB credentials in `.streamlit/secrets.toml` (local) and in
Streamlit Community Cloud's "Secrets" panel (deployed) — never commit
this file. `db_manager.py` should read from `st.secrets` when running
inside Streamlit, falling back to `os.environ` for non-Streamlit contexts
(e.g. the standalone ETL script).

## 6. Minimum Viable Slice (if time-constrained)

If time runs short, prioritize in this order:
1. One working write page (Onboard Employee) proving OLTP round-trip.
2. One working dashboard (Top Performers, since `DENSE_RANK` is an explicit
   requirement) proving OLAP round-trip.
3. The SCD2-triggering update flow — this is the single most
   differentiating feature of the whole project; don't leave it for last.
