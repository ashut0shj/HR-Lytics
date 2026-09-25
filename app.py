import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from src.db_wrapper import DBWrapper
from src.managers import EmployeeManager, DepartmentManager, ProjectManager, ReviewManager, AnalyticsManager, ExplorerManager
from src.models import Employee, Project, Review

st.set_page_config(page_title="HR-Lytics Dashboard", layout="wide")

db_health = DBWrapper()
if not db_health.is_healthy():
    st.title("HR-Lytics Enterprise Platform")
    st.error("⚠️ Database connection failed")
    st.info(
        "We couldn't connect to the database right now.\n\n"
        "- **Using Aiven Cloud?** Free or trial tier databases pause automatically when idle. Head over to the [Aiven Console](https://console.aiven.io/), click **Power on**, and wait about a minute.\n"
        "- **Running locally?** Make sure your local MySQL service is running and credentials in `.env` match."
    )
    if st.button("🔄 Retry Connection"):
        st.cache_resource.clear()
        st.rerun()
    st.stop()

@st.cache_resource
def get_managers():
    return {
        "employee": EmployeeManager(),
        "department": DepartmentManager(),
        "project": ProjectManager(),
        "review": ReviewManager(),
        "analytics": AnalyticsManager(),
        "explorer": ExplorerManager(),
    }

managers = get_managers()

title_col, refresh_col = st.columns([5, 1])
title_col.title("HR-Lytics Enterprise Platform")
with refresh_col:
    st.write("")
    if st.button("Refresh OLAP", help="Re-run the ETL so new OLTP data (onboarding, department changes, reviews) shows up in the analytics dashboard"):
        with st.spinner("Syncing OLTP → OLAP..."):
            ok = managers["analytics"].refresh_olap()
        if ok:
            st.success("OLAP refreshed.")
        else:
            st.error("Refresh failed — check logs.")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Analytics Dashboard", "Onboard Employee", "Projects & Assignments", "Submit Review", "Data Explorer"]
)

if page == "Analytics Dashboard":
    am = managers["analytics"]

    col1, col2, col3 = st.columns(3)
    headcount_df = am.headcount_by_department()
    attrition_df = am.attrition_overview()

    total_employees = int(headcount_df["headcount"].sum()) if not headcount_df.empty else 0
    if not attrition_df.empty and "attrition" in attrition_df.columns:
        attrition_yes = attrition_df.loc[attrition_df["attrition"] == "Yes", "employee_count"]
        attrition_rate = round(100 * attrition_yes.sum() / total_employees, 1) if total_employees else 0
        avg_income = attrition_df["avg_income"].mean()
        # Weighted average: sum(count * avg_income) / total, not mean of group averages
        weighted_sum = (attrition_df["employee_count"] * attrition_df["avg_income"]).sum()
        avg_income = weighted_sum / attrition_df["employee_count"].sum() if attrition_df["employee_count"].sum() > 0 else 0
    else:
        attrition_rate = 0
        avg_income = 0

    col1.metric("Total Employees", f"{total_employees:,}")
    col2.metric("Attrition Rate", f"{attrition_rate}%")
    col3.metric("Avg Monthly Income", f"${avg_income:,.0f}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Headcount by Department")
        if not headcount_df.empty:
            fig = px.bar(headcount_df, x="department_name", y="headcount", color="department_name")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Attrition Breakdown")
        if not attrition_df.empty:
            fig = px.pie(attrition_df, names="attrition", values="employee_count", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Year-over-Year Performance Trend")
    trend_df = am.year_over_year_trend()
    if not trend_df.empty:
        fig = px.line(
            trend_df, x="year", y=["avg_performance", "avg_job_satisfaction"],
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No review data yet.")

    st.divider()
    st.subheader("Top Performers by Department")
    top_n = st.slider("Show top N per department", 1, 10, 3)
    top_df = am.top_performers_by_department(top_n)
    st.dataframe(top_df, use_container_width=True)

    st.divider()
    st.subheader("Average Salary by Job Role")
    salary_df = am.salary_by_job_role()
    if not salary_df.empty:
        fig = px.bar(salary_df, x="job_role", y="avg_income", color="job_role")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("SCD Type 2 Change History")
    hist_df = am.scd2_change_history(limit=25)
    st.dataframe(hist_df, use_container_width=True)

    st.divider()
    st.subheader("Attrition Risk Early Warning")
    risk_df = am.attrition_risk()
    if not risk_df.empty:
        crit_count = int((risk_df["attrition_risk_tier"] == "Critical Risk").sum())
        high_count = int((risk_df["attrition_risk_tier"] == "High Risk").sum())
        rcol1, rcol2 = st.columns(2)
        rcol1.metric("Critical Risk Employees", crit_count)
        rcol2.metric("High Risk Employees", high_count)
        st.dataframe(risk_df, use_container_width=True)
    else:
        st.info("No review or employee data available for attrition risk calculation.")


elif page == "Onboard Employee":
    st.subheader("Onboard a New Employee")
    em = managers["employee"]
    dm = managers["department"]
    am = managers["analytics"]

    departments = dm.get_all()
    dept_names = [d["department_name"] for d in departments] if departments else ["General"]

    with st.form("onboard_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name")
            last_name = st.text_input("Last name")
            email = st.text_input("Email")
            gender = st.selectbox("Gender", ["Male", "Female"])
            age = st.number_input("Age", min_value=18, max_value=70, value=28)
        with c2:
            department = st.selectbox("Department", dept_names)
            job_role = st.text_input("Job role", value="Analyst")
            job_level = st.slider("Job level", 1, 5, 1)
            monthly_income = st.number_input("Monthly income ($)", min_value=1000, value=4000, step=100)
            hire_date = st.date_input("Hire date", value=date.today())

        submitted = st.form_submit_button("Onboard Employee")

    if submitted:
        if not first_name or not last_name or not email:
            st.error("First name, last name, and email are required.")
        elif not first_name.replace(" ", "").isalpha() or not last_name.replace(" ", "").isalpha():
            st.error("Names should contain characters only.")
        elif not str(age).isdigit():
            st.error("Age must be a number between 18 and 70.")
        else:
            dept_id = dm.create_if_missing(department)
            new_emp = Employee(
                first_name=first_name, last_name=last_name, email=email,
                gender=gender, age=int(age), department_id=dept_id, job_role=job_role,
                job_level=job_level, monthly_income=monthly_income, hire_date=hire_date,
                attrition="No", employee_id=em.next_id(),
            )
            ok = em.create(new_emp)
            if ok:
                st.success(f"Onboarded {new_emp.full_name} into {department}")
            else:
                st.error("Error saving employee.")

    st.divider()
    st.subheader("Update an Employee's Department")
    all_emps = em.get_all(limit=500)
    if all_emps:
        emp_options = {f'{e["first_name"]} {e["last_name"]} (ID {e["employee_id"]})': e["employee_id"] for e in all_emps}
        chosen = st.selectbox("Employee", list(emp_options.keys()))
        new_dept = st.selectbox("New department", dept_names, key="scd_dept")
        if st.button("Apply Department Change"):
            emp_id = emp_options[chosen]
            dept_id = dm.create_if_missing(new_dept)
            em.update_department(emp_id, dept_id)
            am.apply_scd2_department_change(emp_id, new_dept)
            st.success(f"Moved employee to {new_dept}.")

    st.divider()
    st.subheader("Recent Employees")
    st.dataframe(pd.DataFrame(em.get_all(limit=50)), use_container_width=True)


elif page == "Projects & Assignments":
    st.subheader("Create a Project")
    pm = managers["project"]
    dm = managers["department"]
    em = managers["employee"]

    departments = dm.get_all()
    dept_names = [d["department_name"] for d in departments] if departments else ["General"]

    with st.form("project_form"):
        proj_name = st.text_input("Project name")
        proj_dept = st.selectbox("Department", dept_names)
        start = st.date_input("Start date", value=date.today())
        end = st.date_input("End date (optional)", value=None)
        proj_submitted = st.form_submit_button("Create Project")

    if proj_submitted:
        if not proj_name:
            st.error("Project name is required.")
        else:
            dept_id = dm.create_if_missing(proj_dept)
            proj = Project(project_name=proj_name, department_id=dept_id, start_date=start, end_date=end)
            if pm.create(proj):
                st.success(f"Created project '{proj_name}'")
            else:
                st.error("Error creating project.")

    st.divider()
    st.subheader("Assign an Employee to a Project")
    all_emps = em.get_all(limit=500)
    all_projects = pm.get_all()
    if all_emps and all_projects:
        emp_options = {f'{e["first_name"]} {e["last_name"]} (ID {e["employee_id"]})': e["employee_id"] for e in all_emps}
        proj_options = {p["project_name"]: p["project_id"] for p in all_projects}

        chosen_emp = st.selectbox("Employee", list(emp_options.keys()))
        chosen_proj = st.selectbox("Project", list(proj_options.keys()))
        role = st.text_input("Role on project", value="Contributor")

        if st.button("Assign"):
            ok = pm.assign_employee(emp_options[chosen_emp], proj_options[chosen_proj], role)
            if ok:
                st.success(f"Assigned {chosen_emp} to {chosen_proj} as {role}")
            else:
                st.error("Assignment failed.")
    else:
        st.info("Create at least one employee and one project first.")

    st.divider()
    st.subheader("All Projects")
    st.dataframe(pd.DataFrame(pm.get_all()), use_container_width=True)


elif page == "Submit Review":
    st.subheader("Submit a Performance Review")
    em = managers["employee"]
    rm = managers["review"]

    all_emps = em.get_all(limit=500)
    if not all_emps:
        st.info("No employees yet.")
    else:
        emp_options = {f'{e["first_name"]} {e["last_name"]} (ID {e["employee_id"]})': e["employee_id"] for e in all_emps}

        with st.form("review_form"):
            chosen_emp = st.selectbox("Employee", list(emp_options.keys()))
            review_date = st.date_input("Review date", value=date.today())
            performance = st.slider("Performance rating", 1, 4, 3)
            job_sat = st.slider("Job satisfaction", 1, 4, 3)
            env_sat = st.slider("Environment satisfaction", 1, 4, 3)
            rel_sat = st.slider("Relationship satisfaction", 1, 4, 3)
            wlb = st.slider("Work-life balance", 1, 4, 3)
            review_submitted = st.form_submit_button("Submit Review")

        if review_submitted:
            review = Review(
                employee_id=emp_options[chosen_emp], review_date=review_date,
                performance_rating=performance, job_satisfaction=job_sat,
                environment_satisfaction=env_sat, relationship_satisfaction=rel_sat,
                work_life_balance=wlb,
            )
            if rm.create(review):
                st.success(f"Review submitted (score: {review.overall_score()}/4)")
            else:
                st.error("Error saving review.")

        st.divider()
        st.subheader("Review History")
        emp_id_for_history = emp_options[st.selectbox("View history for", list(emp_options.keys()), key="hist_emp")]
        st.dataframe(pd.DataFrame(rm.get_for_employee(emp_id_for_history)), use_container_width=True)

elif page == "Data Explorer":
    st.subheader("OLTP Database Explorer")
    st.markdown("Filter operational tables.")
    
    ex = managers["explorer"]
    
    # List of tables in hr_oltp
    tables = ["staging_employees", "staging_employee_history", "employees", "departments", "projects", "assignments", "reviews"]
    table = st.selectbox("Select Table to View", tables)
    
    # Fetch columns for the selected table to build dynamic filters
    columns = ex.get_columns(table)
    
    st.write("### Filter Data")
    c1, c2, c3 = st.columns([2, 1, 3])
    with c1:
        filter_col = st.selectbox("Filter Column", ["None"] + columns)
    with c2:
        operator = st.selectbox("Operator", ["=", ">", "<", ">=", "<=", "LIKE", "!=:"])
    with c3:
        val = st.text_input("Value", placeholder="Enter filter value...")
        
    limit = st.slider("Row Limit", min_value=10, max_value=5000, value=100)
    
    if st.button("Execute Query"):
        with st.spinner(f"Querying {table}..."):
            result_df = ex.filter_table(table, filter_col, operator, val, limit)
            if not result_df.empty:
                st.success(f"Returned {len(result_df)} rows")
                st.dataframe(result_df, use_container_width=True)
            else:
                st.warning("No rows match the given filter criteria or table is empty.")
