import os
import random
from datetime import date, timedelta
import pandas as pd
from faker import Faker

TARGET_ROWS = 100_000
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

NAME_POOL_SIZE = 8000

def clone_employees(base_df: pd.DataFrame, target_rows: int) -> pd.DataFrame:
    repeats_needed = -(-target_rows // len(base_df))

    big_df = pd.concat([base_df] * repeats_needed, ignore_index=True)
    big_df = big_df.sample(n=target_rows, random_state=RANDOM_SEED).reset_index(drop=True)

    big_df.insert(0, "employee_id", range(1, len(big_df) + 1))

    # Generating a name with Faker per row is the slow part at 1M rows.
    # A pool of a few thousand unique-ish names, sampled per row, gives the
    # same realistic variety for a fraction of the Faker calls.
    male_pool = [fake.first_name_male() for _ in range(NAME_POOL_SIZE)]
    female_pool = [fake.first_name_female() for _ in range(NAME_POOL_SIZE)]
    last_pool = [fake.last_name() for _ in range(NAME_POOL_SIZE)]

    is_male = (big_df["Gender"] == "Male").to_numpy()
    n = len(big_df)
    first_names = [
        random.choice(male_pool) if male else random.choice(female_pool)
        for male in is_male
    ]
    last_names = [random.choice(last_pool) for _ in range(n)]
    # employee_id suffix guarantees a unique email without scanning a growing set
    emails = [
        f"{f}.{l}.{emp_id}@company.com".lower()
        for f, l, emp_id in zip(first_names, last_names, big_df["employee_id"])
    ]
    hire_dates = [random_hire_date() for _ in range(n)]

    big_df["first_name"] = first_names
    big_df["last_name"] = last_names
    big_df["email"] = emails
    big_df["hire_date"] = hire_dates

    return big_df

def build_scd2_tables(current_df: pd.DataFrame):
    n_changed = int(len(current_df) * HISTORY_FRACTION)
    changed_ids = current_df["employee_id"].sample(n=n_changed, random_state=RANDOM_SEED)
    changed_mask = current_df["employee_id"].isin(set(changed_ids))

    departments = current_df["Department"].unique().tolist()
    job_roles = current_df["JobRole"].unique().tolist()

    changed_df = current_df.loc[changed_mask].copy()
    m = len(changed_df)

    level_drop = [random.choice([0, 1]) for _ in range(m)]
    income_factor = [random.uniform(0.75, 0.92) for _ in range(m)]
    change_dates = [date.today() - timedelta(days=random.randint(400, 900)) for _ in range(m)]

    history_df = changed_df.copy()
    history_df["Department"] = [random.choice(departments) for _ in range(m)]
    history_df["JobRole"] = [random.choice(job_roles) for _ in range(m)]
    history_df["JobLevel"] = [max(1, jl - drop) for jl, drop in zip(changed_df["JobLevel"], level_drop)]
    history_df["MonthlyIncome"] = [int(mi * f) for mi, f in zip(changed_df["MonthlyIncome"], income_factor)]
    history_df["scd_start_date"] = changed_df["hire_date"].values
    history_df["scd_end_date"] = change_dates
    history_df["is_current"] = 0

    current_df["scd_start_date"] = current_df["hire_date"]
    current_df.loc[changed_mask, "scd_start_date"] = pd.Series(change_dates, index=changed_df.index)
    current_df["scd_end_date"] = None
    current_df["is_current"] = 1

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

