from __future__ import annotations

import calendar
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from app.models.case import (
    BenefitComparisonResult,
    BenefitPlan,
    EmployeeProfile,
    ExpenseCheckResult,
    LeaveBalanceResult,
    RemoteWorkCheckResult,
)


def _round_half_day(value: Decimal) -> Decimal:
    return (value * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2


def _normalise_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


class CaseDataService:
    """Read-only access to synthetic employee and HR reference data."""

    def __init__(self, employee_path: Path, reference_path: Path) -> None:
        employee_data = json.loads(employee_path.read_text(encoding="utf-8"))
        self.employees = {
            item["employee_id"]: EmployeeProfile.model_validate(item)
            for item in employee_data["employees"]
        }
        self.reference_data: dict[str, Any] = json.loads(
            reference_path.read_text(encoding="utf-8")
        )

    def get_employee_profile(self, employee_id: str) -> EmployeeProfile:
        try:
            return self.employees[employee_id.upper()]
        except KeyError as exc:
            raise ValueError(f"Unknown synthetic employee ID: {employee_id}") from exc

    def calculate_leave_balance(
        self, employee_id: str, as_of_date: date
    ) -> LeaveBalanceResult:
        employee = self.get_employee_profile(employee_id)
        policy_year = as_of_date.year
        year_start = date(policy_year, 1, 1)
        year_end = date(policy_year, 12, 31)
        employment_start = max(employee.start_date, year_start)

        if employment_start > year_end:
            raise ValueError(f"{employee_id} had not started by policy year {policy_year}")

        days_in_year = Decimal((year_end - year_start).days + 1)
        employed_days = Decimal((year_end - employment_start).days + 1)
        full_year = Decimal("20") * Decimal(str(employee.work_schedule_percentage))
        projected = _round_half_day(full_year * employed_days / days_in_year)

        eligible_months = 13 - employment_start.month
        credited_months = 0
        for month in range(employment_start.month, 13):
            month_end = date(policy_year, month, calendar.monthrange(policy_year, month)[1])
            if month_end <= as_of_date:
                credited_months += 1

        accrued = (
            projected * Decimal(credited_months) / Decimal(eligible_months)
            if eligible_months
            else Decimal("0")
        )

        approved_taken = Decimal("0")
        approved_future = Decimal("0")
        for entry in employee.leave_entries:
            if entry.leave_type != "annual" or entry.status != "approved":
                continue
            if entry.start_date.year != policy_year:
                continue
            if entry.start_date <= as_of_date:
                approved_taken += Decimal(str(entry.days))
            else:
                approved_future += Decimal(str(entry.days))

        carryover = Decimal(str(employee.carryover_days))
        if as_of_date > date(policy_year, 3, 31):
            carryover = Decimal("0")

        available = accrued + carryover - approved_taken - approved_future
        explanation = [
            f"Projected entitlement uses {int(employed_days)} employed calendar days out of {int(days_in_year)}.",
            f"{credited_months} of {eligible_months} eligible monthly credits have posted by {as_of_date.isoformat()}.",
            "Only approved annual leave is deducted; pending or cancelled requests are excluded.",
        ]

        return LeaveBalanceResult(
            employee_id=employee.employee_id,
            as_of_date=as_of_date,
            policy_year=policy_year,
            projected_entitlement=float(projected),
            accrued_leave=round(float(accrued), 2),
            valid_carryover=float(carryover),
            approved_leave_taken=float(approved_taken),
            approved_future_leave=float(approved_future),
            available_balance=round(float(available), 2),
            in_probation=as_of_date <= employee.probation_end_date,
            explanation=explanation,
        )

    def check_expense_eligibility(
        self,
        *,
        category: str,
        amount_hkd: float,
        has_business_purpose: bool,
        has_receipt: bool,
        after_22_00: bool = False,
    ) -> ExpenseCheckResult:
        key = _normalise_key(category)
        categories = self.reference_data["expense_categories"]
        if key not in categories:
            return ExpenseCheckResult(
                category=key,
                amount_hkd=amount_hkd,
                within_standard_limit=False,
                standard_limit_hkd=None,
                required_approvals=["finance_review"],
                required_evidence=["business_purpose", "supporting_evidence"],
                notes=["The category is not defined in the structured expense table."],
            )

        rule = categories[key]
        limit = float(rule["limit_hkd"])
        within_limit = amount_hkd <= limit
        approvals = rule["approvals"] if within_limit else rule["above_limit_approvals"]
        notes: list[str] = []

        if not has_business_purpose:
            notes.append("A valid business purpose is required regardless of amount.")
        if not has_receipt:
            notes.append("Missing evidence requires Finance review and cannot be approved by this tool.")
            approvals = list(dict.fromkeys([*approvals, "finance_review"]))
        if key == "taxi" and after_22_00:
            notes.append(
                "A work-caused journey home after 22:00 can establish a business reason, but does not remove the limit."
            )
        if not within_limit:
            notes.append(f"The amount exceeds the standard HKD {limit:,.0f} limit.")

        return ExpenseCheckResult(
            category=key,
            amount_hkd=amount_hkd,
            within_standard_limit=within_limit and has_business_purpose,
            standard_limit_hkd=limit,
            required_approvals=list(approvals),
            required_evidence=list(rule["evidence"]),
            notes=notes,
        )

    def compare_benefit_plans(self, plan_names: list[str]) -> BenefitComparisonResult:
        available = self.reference_data["benefit_plans"]
        plans: list[BenefitPlan] = []
        for name in plan_names:
            match = next((key for key in available if key.lower() == name.lower()), None)
            if match is None:
                raise ValueError(f"Unknown benefit plan: {name}")
            plans.append(BenefitPlan.model_validate(available[match]))

        differences: list[str] = []
        if len(plans) == 2:
            first, second = plans
            differences = [
                f"{second.name} costs HKD {second.monthly_contribution_hkd - first.monthly_contribution_hkd:,.0f} more per month than {first.name}.",
                f"{second.name} provides HKD {second.outpatient_annual_limit_hkd - first.outpatient_annual_limit_hkd:,.0f} more outpatient cover.",
                f"{second.name} has a specialist co-pay HKD {first.specialist_copay_hkd - second.specialist_copay_hkd:,.0f} lower than {first.name}.",
            ]

        return BenefitComparisonResult(
            plans=plans,
            differences=differences,
            source="HR-BEN-001 §3",
        )

    def check_remote_work_request(
        self,
        *,
        employee_id: str,
        destination: str,
        working_dates: list[date],
        request_date: date,
    ) -> RemoteWorkCheckResult:
        employee = self.get_employee_profile(employee_id)
        destination_key = _normalise_key(destination)
        destination_rule = self.reference_data["destinations"].get(
            destination_key, self.reference_data["destinations"]["unknown"]
        )
        requested_days = len(set(working_dates))
        existing_days = len(
            {day for day in employee.international_remote_work_days if day.year == request_date.year}
        )
        blockers: list[str] = []
        approvals = ["manager", "people_operations"]

        if employee.employment_type != "permanent_employees":
            blockers.append("The standard process is limited to permanent employees.")
        if working_dates and min(working_dates) <= employee.probation_end_date:
            blockers.append("The employee must complete probation before the proposed start date.")
        if requested_days > 10:
            blockers.append("A single trip cannot exceed 10 international remote-working days.")
        if existing_days + requested_days > 20:
            blockers.append("The request would exceed the 20-day annual limit.")
        if working_dates and (min(working_dates) - request_date).days < 30:
            blockers.append("The request provides fewer than 30 calendar days' notice.")
        if destination_rule["status"] != "approved":
            blockers.append(
                f"The destination status is '{destination_rule['status']}' and requires review."
            )
        if employee.restricted_data_access or destination_rule["security_review"]:
            approvals.append("it_security")

        return RemoteWorkCheckResult(
            employee_id=employee.employee_id,
            destination=destination_key,
            requested_working_days=requested_days,
            annual_days_after_request=existing_days + requested_days,
            standard_eligibility=not blockers,
            required_approvals=list(dict.fromkeys(approvals)),
            blockers=blockers,
            notes=[
                "This is a policy pre-check, not an approval.",
                "The result does not confirm immigration, tax, or visa compliance.",
            ],
        )

