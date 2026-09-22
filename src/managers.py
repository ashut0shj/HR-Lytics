from datetime import date
from src.db_wrapper import DBWrapper
from src.query_loader import load_named
from src.models import Employee, Project, Review


class BaseManager:
    def __init__(self):
        self.db = DBWrapper()

    def _safe_query(self, sql, params=None):
        try:
            return self.db.fetch_all(sql, params)
        except Exception as exc:
            print(f"[{self.__class__.__name__}] query error: {exc}")
            return []

    def _safe_execute(self, sql, params=None):
        try:
            return self.db.execute_query(sql, params)
        except Exception as exc:
            print(f"[{self.__class__.__name__}] execute error: {exc}")
            return None


class EmployeeManager(BaseManager):
    def create(self, emp: Employee) -> bool:
        sql = load_named("oltp/employees.sql", "insert a new employee")
        params = {
            "employee_id": emp.employee_id,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "email": emp.email,
            "gender": emp.gender,
            "age": emp.age,
            "department_id": emp.department_id,
            "job_role": emp.job_role,
            "job_level": emp.job_level,
            "monthly_income": emp.monthly_income,
            "hire_date": emp.hire_date.isoformat() if isinstance(emp.hire_date, date) else emp.hire_date,
            "attrition": emp.attrition,
        }
        result = self._safe_execute(sql, params)
        return result is not None

    def get_all(self, limit: int = 200):
        sql = load_named("oltp/employees.sql", "get all employees sorted by newest first")
        return self._safe_query(sql, {"limit": limit})

    def get_by_id(self, employee_id: int):
        sql = load_named("oltp/employees.sql", "get a single employee by id")
        rows = self._safe_query(sql, {"id": employee_id})
        return rows[0] if rows else None

    def update_department(self, employee_id: int, new_department_id: int) -> bool:
        sql = load_named("oltp/employees.sql", "update employee's department")
        result = self._safe_execute(sql, {"dept_id": new_department_id, "emp_id": employee_id})
        return result is not None

    def delete(self, employee_id: int) -> bool:
        sql = load_named("oltp/employees.sql", "delete an employee")
        result = self._safe_execute(sql, {"id": employee_id})
        return result is not None

    def next_id(self) -> int:
        sql = load_named("oltp/employees.sql", "get max employee id for next id generation")
        rows = self._safe_query(sql)
        max_id = rows[0]["max_id"] if rows and rows[0]["max_id"] else 0
        return max_id + 1


class DepartmentManager(BaseManager):
    def get_all(self):
        sql = load_named("oltp/departments.sql", "get all departments")
        return self._safe_query(sql)

    def create_if_missing(self, name: str) -> int:
        sql = load_named("oltp/departments.sql", "find a department by name")
        existing = self._safe_query(sql, {"n": name})
        if existing:
            return existing[0]["department_id"]
        self._safe_execute(load_named("oltp/departments.sql", "insert a new department"), {"n": name})
        row = self._safe_query(sql, {"n": name})
        return row[0]["department_id"] if row else None


class ProjectManager(BaseManager):
    def create(self, proj: Project) -> bool:
        sql = load_named("oltp/projects.sql", "insert a new project")
        params = {
            "name": proj.project_name,
            "dept_id": proj.department_id,
            "start": proj.start_date.isoformat() if isinstance(proj.start_date, date) else proj.start_date,
            "end": proj.end_date.isoformat() if isinstance(proj.end_date, date) else proj.end_date,
        }
        result = self._safe_execute(sql, params)
        return result is not None

    def get_all(self):
        sql = load_named("oltp/projects.sql", "get all projects newest first")
        return self._safe_query(sql)

    def assign_employee(self, employee_id: int, project_id: int, role: str) -> bool:
        sql = load_named("oltp/projects.sql", "assign an employee to a project")
        result = self._safe_execute(
            sql,
            {"emp": employee_id, "proj": project_id, "role": role, "today": date.today().isoformat()},
        )
        return result is not None


class ReviewManager(BaseManager):
    def create(self, review: Review) -> bool:
        sql = load_named("oltp/reviews.sql", "insert a performance review")
        params = {
            "emp_id": review.employee_id,
            "rdate": review.review_date.isoformat() if isinstance(review.review_date, date) else review.review_date,
            "perf": review.performance_rating,
            "job_sat": review.job_satisfaction,
            "env_sat": review.environment_satisfaction,
            "rel_sat": review.relationship_satisfaction,
            "wlb": review.work_life_balance,
        }
        result = self._safe_execute(sql, params)
        return result is not None

    def get_for_employee(self, employee_id: int):
        sql = load_named("oltp/reviews.sql", "get all reviews for an employee")
        return self._safe_query(sql, {"id": employee_id})


class AnalyticsManager(BaseManager):
    def headcount_by_department(self):
        sql = load_named("olap/analytics.sql", "headcount per department (current employees only)")
        return self.db.query_df(sql)

    def top_performers_by_department(self, top_n: int = 3):
        sql = load_named("olap/analytics.sql", "top performers ranked per department using window function")
        sql = sql.format(top_n=int(top_n))
        return self.db.query_df(sql)

    def year_over_year_trend(self):
        sql = load_named("olap/analytics.sql", "year over year avg performance and satisfaction trend")
        return self.db.query_df(sql)

    def attrition_overview(self):
        sql = load_named("olap/analytics.sql", "attrition breakdown with average income")
        return self.db.query_df(sql)

    def attrition_risk(self):
        sql = load_named("olap/analytics.sql", "attrition risk by satisfaction and department benchmarks")
        return self.db.query_df(sql)

    def salary_by_job_role(self):
        sql = load_named("olap/analytics.sql", "average salary per job role")
        return self.db.query_df(sql)

    def scd2_change_history(self, limit: int = 50):
        sql = load_named("olap/analytics.sql", "employees who changed departments (scd2 history rows)")
        sql = sql.format(limit=int(limit))
        return self.db.query_df(sql)

    def apply_scd2_department_change(self, employee_id: int, new_department: str) -> bool:
        try:
            today = date.today().isoformat()

            self.db.execute_query(
                load_named("olap/analytics.sql", "close the current dim_employee row before inserting a new one"),
                {"yesterday": today, "emp_id": employee_id}
            )

            rows = self.db.fetch_all(
                load_named("olap/analytics.sql", "fetch old dim_employee row to carry attributes forward"),
                {"emp_id": employee_id}
            )

            if not rows:
                return False

            row = rows[0]

            self.db.execute_query(
                load_named("olap/analytics.sql", "insert updated current row for scd2 department change"),
                {
                    "emp_id": employee_id, "fn": row["first_name"], "ln": row["last_name"],
                    "gender": row["gender"], "age": row["age"], "dept": new_department,
                    "role": row["job_role"], "level": row["job_level"],
                    "income": row["monthly_income"], "attr": row["attrition"], "start": today,
                }
            )
            return True
        except Exception as exc:
            print(f"SCD2 update failed: {exc}")
            return False

    def refresh_olap(self) -> bool:
        ok = True
        ok &= self.db.call_procedure("hr_olap.sp_load_dim_department()")
        ok &= self.db.call_procedure("hr_olap.sp_load_dim_project()")
        ok &= self.db.call_procedure("hr_olap.sp_load_dim_employee_scd2()")
        ok &= self.db.call_procedure("hr_olap.sp_load_dim_employee_incremental()")
        ok &= self.db.call_procedure("hr_olap.sp_load_fact_performance_reviews()")
        ok &= self.db.call_procedure("hr_olap.sp_load_fact_reviews_incremental()")
        return ok


class ExplorerManager(BaseManager):
    def get_columns(self, table: str) -> list:
        cols_df = self.db.query_df(f"SHOW COLUMNS FROM {table}")
        return cols_df["Field"].tolist() if not cols_df.empty else []

    def filter_table(self, table: str, filter_col: str, operator: str, val: str, limit: int):
        if filter_col != "None" and val != "":
            if operator == "LIKE":
                query = f"SELECT * FROM {table} WHERE {filter_col} LIKE %s LIMIT %s"
                params = (f"%{val}%", int(limit))
            else:
                op = "!=" if operator == "!=:" else operator
                query = f"SELECT * FROM {table} WHERE {filter_col} {op} %s LIMIT %s"
                params = (val, int(limit))
        else:
            query = f"SELECT * FROM {table} LIMIT %s"
            params = (int(limit),)

        return self.db.query_df(query, params)

