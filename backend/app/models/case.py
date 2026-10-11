from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class LeaveEntry(BaseModel):
    start_date: date
    days: float = Field(gt=0)
    status: Literal["pending", "approved", "cancelled"]
    leave_type: str = "annual"


class EmployeeProfile(BaseModel):
    employee_id: str
    display_name: str
    work_location: str
    employment_type: str
    work_schedule_percentage: float = Field(gt=0, le=1)
    start_date: date
    probation_end_date: date
    manager_id: str
    department: str
    job_level: str
    benefit_plan: str
    role_work_arrangement: str
    restricted_data_access: bool = False
    carryover_days: float = 0
    leave_entries: list[LeaveEntry] = Field(default_factory=list)
    international_remote_work_days: list[date] = Field(default_factory=list)


class LeaveBalanceResult(BaseModel):
    employee_id: str
    as_of_date: date
    policy_year: int
    projected_entitlement: float
    accrued_leave: float
    valid_carryover: float
    approved_leave_taken: float
    approved_future_leave: float
    available_balance: float
    in_probation: bool
    explanation: list[str]


class ExpenseCheckResult(BaseModel):
    category: str
    amount_hkd: float
    within_standard_limit: bool
    standard_limit_hkd: float | None
    required_approvals: list[str]
    required_evidence: list[str]
    notes: list[str]


class BenefitPlan(BaseModel):
    name: str
    monthly_contribution_hkd: float
    outpatient_annual_limit_hkd: float
    specialist_copay_hkd: float
    dental_annual_limit_hkd: float
    vision_annual_limit_hkd: float | None
    dependant_rule: str


class BenefitComparisonResult(BaseModel):
    plans: list[BenefitPlan]
    differences: list[str]
    source: str


class RemoteWorkCheckResult(BaseModel):
    employee_id: str
    destination: str
    requested_working_days: int
    annual_days_after_request: int
    standard_eligibility: bool
    required_approvals: list[str]
    blockers: list[str]
    notes: list[str]

