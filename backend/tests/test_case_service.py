from datetime import date

import pytest

from app.config import REPOSITORY_ROOT
from app.services.case_service import CaseDataService


@pytest.fixture
def service() -> CaseDataService:
    return CaseDataService(
        REPOSITORY_ROOT / "data" / "structured" / "employees.json",
        REPOSITORY_ROOT / "data" / "structured" / "reference-data.json",
    )


def test_first_year_leave_is_prorated_and_accrued_monthly(service: CaseDataService) -> None:
    result = service.calculate_leave_balance("NS-1042", date(2026, 10, 11))

    assert result.projected_entitlement == 11.0
    assert result.accrued_leave == 6.29
    assert result.approved_leave_taken == 4.0
    assert result.available_balance == 2.29
    assert result.in_probation is False


def test_expense_above_limit_keeps_late_night_exception_separate(
    service: CaseDataService,
) -> None:
    result = service.check_expense_eligibility(
        category="taxi",
        amount_hkd=620,
        has_business_purpose=True,
        has_receipt=True,
        after_22_00=True,
    )

    assert result.within_standard_limit is False
    assert result.standard_limit_hkd == 500
    assert result.required_approvals == ["manager", "department_head"]
    assert any("does not remove the limit" in note for note in result.notes)


def test_benefit_comparison_uses_structured_values(service: CaseDataService) -> None:
    result = service.compare_benefit_plans(["Standard", "Premium"])

    assert [plan.name for plan in result.plans] == ["Standard", "Premium"]
    assert result.plans[1].monthly_contribution_hkd == 420
    assert result.source == "HR-BEN-001 §3"


def test_remote_work_flags_trip_over_ten_days(service: CaseDataService) -> None:
    dates = [date(2026, 11, day) for day in range(2, 17)]
    result = service.check_remote_work_request(
        employee_id="NS-1077",
        destination="Japan",
        working_dates=dates,
        request_date=date(2026, 9, 1),
    )

    assert result.standard_eligibility is False
    assert result.annual_days_after_request == 20
    assert any("single trip" in blocker for blocker in result.blockers)


def test_unknown_employee_is_explicit(service: CaseDataService) -> None:
    with pytest.raises(ValueError, match="Unknown synthetic employee ID"):
        service.get_employee_profile("NS-9999")

