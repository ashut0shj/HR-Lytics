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
├── Dockerfile                  # Container definition for Streamlit app
├── docker-compose.yml          # Multi-container orchestration (App + MySQL)
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

## Quickstart with Docker (Recommended)

The easiest way to run HR-Lytics without installing or configuring a local MySQL server is using Docker Compose. It automatically spins up MySQL 8.0, executes the initial database schemas and stored procedures, and starts the Streamlit dashboard.

### 1. Run with Docker Compose

```bash
docker compose up --build
```

### 2. Access the Application

Open your browser and navigate to:
```text
http://localhost:8501
```

To stop the containers:
```bash
docker compose down
```

---

## Manual Local Setup

If you prefer to run the application directly on your host machine with an existing MySQL instance:

### 1. Prerequisites

* **Python 3.10+**
* **MySQL Server 8.0+**
* **pip / venv**

### 2. Set Up Virtual Environment

```bash
# Clone repository
git clone <repo-url>
cd HR-Lytics

# Create & activate virtual environment
python -m venv venv

# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Database Credentials

Create `.env` in the root directory:

```bash
cp .env.example .env
```

Set your credentials:

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hr_oltp
DB_PORT=3306
```

### 4. Database Initialization

Run the initialization scripts in order:

```bash
mysql -u root -p < sql/01_oltp_schema.sql
mysql -u root -p < sql/02_olap_schema.sql
mysql -u root -p < sql/03_etl_procedures.sql
```

### 5. Launch Application

```bash
streamlit run app.py
```

Access the UI at `http://localhost:8501`.

---

## Synthetic Data Generation (Optional)

To populate the warehouse with high-volume synthetic employee records:

1. Place `WA_Fn-UseC_-HR-Employee-Attrition.csv` into `dataset/`.
2. Generate synthetic records:

```bash
python src/synthesizer/generate_data.py
```

3. Load the staging CSVs (`staging_employees.csv` & `staging_employee_history.csv`) into `hr_oltp`, then run the ETL procedures:

```sql
USE hr_olap;

CALL sp_load_dim_date('2015-01-01', '2027-12-31');
CALL sp_load_dim_department();
CALL sp_load_dim_project();
CALL sp_load_dim_employee_scd2();
CALL sp_load_fact_performance_reviews();
```

---

## Application Usage

* **Analytics Dashboard**: Real-time organizational KPIs, compensation distributions, attrition metrics, and SCD Type 2 history logs.
* **Onboard Employee**: Add new employees or update existing employee departments (triggers an automated SCD Type 2 transition).
* **Projects & Assignments**: Create projects and allocate staff with roles.
* **Submit Review**: Record employee performance appraisals across 5 core dimensions.

---

## Tech Stack

* **Frontend / Dashboard**: Streamlit, Plotly Express
* **Backend**: Python (OOP Data Access Layer)
* **Database**: MySQL (`mysql-connector-python`)
* **Data Manipulation**: Pandas, NumPy
* **Data Synthesis**: Faker
* **Containerization**: Docker, Docker Compose
* **Configuration**: python-dotenv
