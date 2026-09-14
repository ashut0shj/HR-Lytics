# HR-Lytics

An enterprise-grade HR analytics platform and data warehouse built with Python, MySQL, and Streamlit. It combines an operational (OLTP) database for managing employees, projects, and performance evaluations with an analytical (OLAP) star schema supporting Slowly Changing Dimensions (SCD Type 2) and SQL window functions.

---

## Features & Capabilities

* **Interactive Analytics Dashboard**: Headcount metrics, attrition rates, compensation by role, longitudinal performance trends, and top performers per department.
* **SCD Type 2 Career Tracking**: Tracks employee transitions (department transfers, title changes) across time while maintaining complete historical integrity.
* **Operational Workflows**:
  * **Employee Onboarding**: Register new staff, assign departments, and configure compensation profiles.
  * **Projects & Staffing**: Create projects and allocate team members with defined responsibilities.
  * **Performance Reviews**: Record multi-metric employee appraisals (performance, job satisfaction, work-life balance).
* **Synthetic Data Generator**: Scales source employee records to 100,000+ realistic profiles using Faker for volume testing.

---

## Project Structure

```text
HR-Lytics/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example                # Sample database configuration
├── src/
│   ├── db/
│   │   ├── db_wrapper.py       # Database connection & transaction handler
│   │   └── query_loader.py     # SQL query management utility
│   ├── managers/
│   │   └── managers.py         # Business logic & Data Access Layer (DAL)
│   ├── models/
│   │   └── models.py           # Data models (Employee, Project, Review)
│   └── synthesizer/
│       └── generate_data.py    # Synthetic data generation script
├── sql/
│   ├── 01_oltp_schema.sql      # Operational schema setup (hr_oltp)
│   ├── 02_olap_schema.sql      # Analytical star schema setup (hr_olap)
│   ├── 03_etl_procedures.sql   # Warehouse loading & SCD Type 2 procedures
│   ├── 04_analytics_queries.sql # Window functions and analytical queries
│   ├── oltp/                   # Parameterized operational queries
│   └── olap/                   # Parameterized reporting queries
├── diagrams/                   # Architecture & schema design references
└── dataset/                    # Raw and generated datasets
```

---

## Prerequisites

* **Python 3.10+**
* **MySQL Server 8.0+**
* **pip / venv**

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repo-url>
cd HR-Lytics
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Database Credentials

Create a `.env` file in the root directory by copying the example:

```bash
cp .env.example .env
```

Configure the environment variables with your MySQL credentials:

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hr_oltp
DB_PORT=3306
```

---

## Database Initialization

Run the following SQL scripts in order using your preferred MySQL client (MySQL CLI or MySQL Workbench):

```bash
mysql -u root -p < sql/01_oltp_schema.sql
mysql -u root -p < sql/02_olap_schema.sql
mysql -u root -p < sql/03_etl_procedures.sql
```

* `01_oltp_schema.sql`: Sets up the normalized operational database (`hr_oltp`) and staging tables.
* `02_olap_schema.sql`: Sets up the star schema data warehouse (`hr_olap`) with dimensions and facts.
* `03_etl_procedures.sql`: Creates stored procedures for warehouse population and SCD Type 2 handling.

---

## Synthetic Data Generation (Optional)

To scale and populate the warehouse with high-volume synthetic employee data:

1. Ensure the IBM HR attrition dataset (`WA_Fn-UseC_-HR-Employee-Attrition.csv`) is present in the `dataset/` directory.
2. Run the synthesizer:

```bash
python src/synthesizer/generate_data.py
```

This generates `dataset/staging_employees.csv` and `dataset/staging_employee_history.csv`.

3. Load the generated staging data into `hr_oltp`, then run the ETL procedures in MySQL:

```sql
USE hr_olap;

CALL sp_load_dim_date('2015-01-01', '2027-12-31');
CALL sp_load_dim_department();
CALL sp_load_dim_project();
CALL sp_load_dim_employee_scd2();
CALL sp_load_fact_performance_reviews();
```

---

## Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Once running, access the dashboard in your web browser at:
`http://localhost:8501`

---

## Application Usage

* **Analytics Dashboard**: View real-time organizational KPIs, salary distributions, attrition metrics, and SCD Type 2 historical logs.
* **Onboard Employee**: Add a new employee into the operational database or update an existing employee's department to trigger an SCD Type 2 audit transition.
* **Projects & Assignments**: Register new projects and assign employees with defined project roles.
* **Submit Review**: Record structured performance evaluations and view past review records.

---

## Tech Stack

* **Frontend / Dashboard**: Streamlit, Plotly Express
* **Backend**: Python (OOP Data Access Layer)
* **Database**: MySQL (`mysql-connector-python`)
* **Data Manipulation**: Pandas, NumPy
* **Data Synthesis**: Faker
* **Configuration**: python-dotenv
