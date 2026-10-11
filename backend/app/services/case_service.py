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
    LeaveCalculationOutcome,
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
        self,
        *,
        as_of_date: date,
        employee_id: str | None = None,
        start_date: date | None = None,
        start_date_inferred: bool = False,
        work_schedule_percentage: float | None = None,
        leave_taken: float | None = None,
        approved_future_leave: float | None = None,
        carryover_days: float | None = None,
        probation_end_date: date | None = None,
    ) -> LeaveCalculationOutcome:
        """Calculate from either an official demo record or temporary scenario facts."""
        normalized_employee_id = employee_id.strip().upper() if employee_id else None
        assumptions: list[str] = []

        if normalized_employee_id:
            try:
                employee = self.get_employee_profile(normalized_employee_id)
            except ValueError as exc:
                return LeaveCalculationOutcome(
                    status="invalid_input",
                    known_facts={"employee_id": normalized_employee_id},
                    message=str(exc),
                )

            start_date = employee.start_date
            work_schedule_percentage = employee.work_schedule_percentage
            approved_leave_taken = 0
            approved_future_leave = 0
            for entry in employee.leave_entries:
                if (
                    entry.leave_type != "annual"
                    or entry.status != "approved"
                    or entry.start_date.year != as_of_date.year
                ):
                    continue
                if entry.start_date <= as_of_date:
                    approved_leave_taken += entry.days
                else:
                    approved_future_leave += entry.days
            carryover_days = employee.carryover_days
            probation_end_date = employee.probation_end_date
            calculation_basis = "employee_record"
        else:
            known_facts = {
                "as_of_date": as_of_date.isoformat(),
                "start_date": start_date.isoformat() if start_date else None,
                "leave_taken": leave_taken,
            }
            missing_fields = []
            if start_date is None:
                missing_fields.append("start_date")
            if leave_taken is None:
                missing_fields.append("leave_taken")
            if missing_fields:
                return LeaveCalculationOutcome(
                    status="needs_input",
                    missing_fields=missing_fields,
                    known_facts=known_facts,
                    message="More scenario information is required before leave can be calculated.",
                )

            if work_schedule_percentage is None:
                work_schedule_percentage = 1.0
                assumptions.append("Full-time work schedule (100%).")
            approved_leave_taken = leave_taken
            assumptions.append(
                "Reported leave already taken is treated as approved annual leave."
            )
            if start_date_inferred:
                assumptions.append(
                    f"The partial joining date was interpreted as {start_date.isoformat()}."
                )
            if approved_future_leave is None:
                approved_future_leave = 0
                assumptions.append("No approved future annual leave.")
            if carryover_days is None:
                carryover_days = 0
                assumptions.append("No carried-over annual leave.")
            calculation_basis = "hypothetical_scenario"

        assert start_date is not None
        assert work_schedule_percentage is not None
        assert approved_leave_taken is not None
        assert approved_future_leave is not None
        assert carryover_days is not None

        if not 0 < work_schedule_percentage <= 1:
            return LeaveCalculationOutcome(
                status="invalid_input",
                known_facts={"work_schedule_percentage": work_schedule_percentage},
                message="work_schedule_percentage must be greater than 0 and at most 1.",
            )
        if min(approved_leave_taken, approved_future_leave, carryover_days) < 0:
            return LeaveCalculationOutcome(
                status="invalid_input",
                message="Leave usage and carryover values cannot be negative.",
            )
        if start_date > as_of_date:
            return LeaveCalculationOutcome(
                status="invalid_input",
                known_facts={
                    "start_date": start_date.isoformat(),
                    "as_of_date": as_of_date.isoformat(),
                },
                message="The employment start date cannot be after the balance as-of date.",
            )

        result = self._calculate_leave_balance(
            employee_id=normalized_employee_id,
            calculation_basis=calculation_basis,
            start_date=start_date,
            as_of_date=as_of_date,
            work_schedule_percentage=work_schedule_percentage,
            approved_leave_taken=approved_leave_taken,
            approved_future_leave=approved_future_leave,
            carryover_days=carryover_days,
            probation_end_date=probation_end_date,
            assumptions=assumptions,
        )
        return LeaveCalculationOutcome(status="success", result=result)

    def _calculate_leave_balance(
        self,
        *,
        employee_id: str | None,
        calculation_basis: str,
        start_date: date,
        as_of_date: date,
        work_schedule_percentage: float,
        approved_leave_taken: float,
        approved_future_leave: float,
        carryover_days: float,
        probation_end_date: date | None,
        assumptions: list[str],
    ) -> LeaveBalanceResult:
        policy_year = as_of_date.year
        year_start = date(policy_year, 1, 1)
        year_end = date(policy_year, 12, 31)
        employment_start = max(start_date, year_start)

        days_in_year = Decimal((year_end - year_start).days + 1)
        employed_days = Decimal((year_end - employment_start).days + 1)
        full_year = Decimal("20") * Decimal(str(work_schedule_percentage))
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

        approved_taken = Decimal(str(approved_leave_taken))
        approved_future = Decimal(str(approved_future_leave))
        carryover = Decimal(str(carryover_days))
        if as_of_date > date(policy_year, 3, 31):
            carryover = Decimal("0")

        available = accrued + carryover - approved_taken - approved_future
        explanation = [
            f"Projected entitlement uses {int(employed_days)} employed calendar days out of {int(days_in_year)}.",
            f"{credited_months} of {eligible_months} eligible monthly credits have posted by {as_of_date.isoformat()}.",
            "Only approved annual leave is deducted; pending or cancelled requests are excluded.",
        ]

        return LeaveBalanceResult(
            employee_id=employee_id,
            calculation_basis=calculation_basis,
            as_of_date=as_of_date,
            policy_year=policy_year,
            projected_entitlement=float(projected),
            accrued_leave=round(float(accrued), 2),
            valid_carryover=float(carryover),
            approved_leave_taken=float(approved_taken),
            approved_future_leave=float(approved_future),
            available_balance=round(float(available), 2),
            in_probation=(
                as_of_date <= probation_end_date if probation_end_date is not None else None
            ),
            assumptions=assumptions,
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

