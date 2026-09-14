import os
import random
from datetime import date, timedelta
import pandas as pd
from faker import Faker

TARGET_ROWS = 105_000
HISTORY_FRACTION = 0.15
RANDOM_SEED = 42

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(THIS_DIR, "..", "..", "dataset", "WA_Fn-UseC_-HR-Employee-Attrition.csv")
OUTPUT_CURRENT_CSV = os.path.join(THIS_DIR, "..", "..", "dataset", "staging_employees.csv")
OUTPUT_HISTORY_CSV = os.path.join(THIS_DIR, "..", "..", "dataset", "staging_employee_history.csv")

random.seed(RANDOM_SEED)
fake = Faker()
Faker.seed(RANDOM_SEED)

def load_base_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_CSV)
    return df

def random_hire_date() -> date:
    days_back = random.randint(30, 15 * 365)
    return date.today() - timedelta(days=days_back)

def clone_employees(base_df: pd.DataFrame, target_rows: int) -> pd.DataFrame:
    repeats_needed = -(-target_rows // len(base_df))

    big_df = pd.concat([base_df] * repeats_needed, ignore_index=True)
    big_df = big_df.sample(n=target_rows, random_state=RANDOM_SEED).reset_index(drop=True)

    big_df.insert(0, "employee_id", range(1, len(big_df) + 1))

    first_names, last_names, emails, hire_dates = [], [], [], []
    used_emails = set()

    for _, row in big_df.iterrows():
        gender = row["Gender"]
        first = fake.first_name_male() if gender == "Male" else fake.first_name_female()
        last = fake.last_name()

        email = f"{first}.{last}@company.com".lower()
        counter = 1
        base_email = email
        while email in used_emails:
            email = base_email.replace("@", f"{counter}@")
            counter += 1
        used_emails.add(email)

        first_names.append(first)
        last_names.append(last)
        emails.append(email)
        hire_dates.append(random_hire_date())

    big_df["first_name"] = first_names
    big_df["last_name"] = last_names
    big_df["email"] = emails
    big_df["hire_date"] = hire_dates

    return big_df

def build_scd2_tables(current_df: pd.DataFrame):
    n_changed = int(len(current_df) * HISTORY_FRACTION)
    changed_ids = current_df["employee_id"].sample(n=n_changed, random_state=RANDOM_SEED)
    changed_set = set(changed_ids)

    history_rows = []
    departments = current_df["Department"].unique().tolist()
    job_roles = current_df["JobRole"].unique().tolist()

    for _, row in current_df.iterrows():
        emp_id = row["employee_id"]

        if emp_id in changed_set:
            old_row = row.copy()
            old_row["Department"] = random.choice(departments)
            old_row["JobRole"] = random.choice(job_roles)
            old_row["JobLevel"] = max(1, row["JobLevel"] - random.choice([0, 1]))
            old_row["MonthlyIncome"] = int(row["MonthlyIncome"] * random.uniform(0.75, 0.92))

            change_date = date.today() - timedelta(days=random.randint(400, 900))
            old_row["scd_start_date"] = row["hire_date"]
            old_row["scd_end_date"] = change_date
            old_row["is_current"] = 0
            history_rows.append(old_row)

            current_df.loc[current_df["employee_id"] == emp_id, "scd_start_date"] = change_date
        else:
            current_df.loc[current_df["employee_id"] == emp_id, "scd_start_date"] = row["hire_date"]

    current_df["scd_end_date"] = None
    current_df["is_current"] = 1

    history_df = pd.DataFrame(history_rows)
    return current_df, history_df

def main():
    try:
        base_df = load_base_data()
        current_df = clone_employees(base_df, TARGET_ROWS)
        current_df, history_df = build_scd2_tables(current_df)

        current_df.to_csv(OUTPUT_CURRENT_CSV, index=False)
        history_df.to_csv(OUTPUT_HISTORY_CSV, index=False)
    except Exception as e:
        print("Error generating data:", e)

if __name__ == "__main__":
    main()

