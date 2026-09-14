from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Employee:
    first_name: str
    last_name: str
    email: str
    gender: str
    age: int
    department_id: int
    job_role: str
    job_level: int
    monthly_income: float
    hire_date: date
    attrition: str = "No"
    employee_id: Optional[int] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def annual_income(self) -> float:
        return round(self.monthly_income * 12, 2)

@dataclass
class Project:
    project_name: str
    department_id: int
    start_date: date
    end_date: Optional[date] = None
    project_id: Optional[int] = None

    def is_active(self) -> bool:
        return self.end_date is None or self.end_date >= date.today()

@dataclass
class Review:
    employee_id: int
    review_date: date
    performance_rating: int
    job_satisfaction: int
    environment_satisfaction: int
    relationship_satisfaction: int
    work_life_balance: int
    review_id: Optional[int] = None

    def overall_score(self) -> float:
        scores = [
            self.performance_rating,
            self.job_satisfaction,
            self.environment_satisfaction,
            self.relationship_satisfaction,
            self.work_life_balance,
        ]
        return round(sum(scores) / len(scores), 2)
