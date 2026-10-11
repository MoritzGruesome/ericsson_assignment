from __future__ import annotations

from datetime import date

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.models.rag import PolicySearchInput
from app.services.case_service import CaseDataService
from app.services.policy_service import PolicySearchService


class EmployeeIdInput(BaseModel):
    employee_id: str = Field(description="Synthetic employee ID, for example NS-1042")


class LeaveBalanceInput(BaseModel):
    as_of_date: date
    employee_id: str | None = Field(
        default=None,
        description="Selected synthetic employee ID. Omit when calculating a conversational scenario.",
    )
    start_date: date | None = Field(
        default=None,
        description="Employment start date stated by the user, required when employee_id is omitted.",
    )
    start_date_inferred: bool = Field(
        default=False,
        description="True when the start year was inferred from a partial date in the request.",
    )
    work_schedule_percentage: float | None = Field(default=None, gt=0, le=1)
    leave_taken: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Annual-leave days the user says were already taken. For a hypothetical estimate, "
            "the tool treats these as approved and discloses that assumption."
        ),
    )
    approved_future_leave: float | None = Field(default=None, ge=0)
    carryover_days: float | None = Field(default=None, ge=0)
    probation_end_date: date | None = None


class ExpenseInput(BaseModel):
    category: str
    amount_hkd: float = Field(gt=0)
    has_business_purpose: bool
    has_receipt: bool
    after_22_00: bool = False


class BenefitComparisonInput(BaseModel):
    plan_names: list[str] = Field(min_length=1, max_length=2)


class RemoteWorkInput(EmployeeIdInput):
    destination: str
    working_dates: list[date] = Field(min_length=1)
    request_date: date


def create_policy_search_tool(service: PolicySearchService) -> StructuredTool:
    def search_policies(**kwargs):
        result = service.search(PolicySearchInput.model_validate(kwargs))
        return result.model_dump(mode="json")

    return StructuredTool.from_function(
        func=search_policies,
        name="search_policies",
        description=(
            "Search active Northstar HR policy sections using OpenAI semantic embeddings and metadata filters. "
            "Use this for policy rules, exceptions, precedence, citations, and escalation requirements."
        ),
        args_schema=PolicySearchInput,
    )


def create_case_tools(service: CaseDataService) -> list[StructuredTool]:
    def get_employee_profile(employee_id: str):
        if not employee_id.strip():
            return {
                "status": "needs_input",
                "missing_fields": ["employee_id"],
                "message": "Select a synthetic employee or use scenario facts instead.",
            }
        try:
            return {
                "status": "success",
                "result": service.get_employee_profile(employee_id).model_dump(mode="json"),
            }
        except ValueError as exc:
            return {"status": "invalid_input", "message": str(exc)}

    return [
        StructuredTool.from_function(
            func=get_employee_profile,
            name="get_employee_profile",
            description="Retrieve the minimum synthetic employee facts needed to analyze a case.",
            args_schema=EmployeeIdInput,
        ),
        StructuredTool.from_function(
            func=lambda **kwargs: service.calculate_leave_balance(**kwargs).model_dump(mode="json"),
            name="calculate_leave_balance",
            description=(
                "Calculate annual leave entitlement, monthly accrual, approved usage, future leave, "
                "carryover, and available balance. Reuse this one tool for either a selected synthetic "
                "employee or a hypothetical scenario built from user-provided facts. The tool returns "
                "success, needs_input, or invalid_input instead of throwing for expected input gaps."
            ),
            args_schema=LeaveBalanceInput,
        ),
        StructuredTool.from_function(
            func=lambda **kwargs: service.check_expense_eligibility(**kwargs).model_dump(
                mode="json"
            ),
            name="check_expense_eligibility",
            description="Check a business expense against structured limits, evidence, and approvals.",
            args_schema=ExpenseInput,
        ),
        StructuredTool.from_function(
            func=lambda plan_names: service.compare_benefit_plans(plan_names).model_dump(mode="json"),
            name="compare_benefit_plans",
            description="Compare the structured features of one or two Northstar benefit plans.",
            args_schema=BenefitComparisonInput,
        ),
        StructuredTool.from_function(
            func=lambda **kwargs: service.check_remote_work_request(**kwargs).model_dump(
                mode="json"
            ),
            name="check_remote_work_request",
            description=(
                "Pre-check an international remote-work request using employee, destination, duration, "
                "annual usage, notice, and security rules."
            ),
            args_schema=RemoteWorkInput,
        ),
    ]

