"""
Pins the wire-format behavior of income DTO enums.

These tests must keep passing across the (str, Enum) → StrEnum
migration. They cover the only thing that matters for the upstream
API contract: the exact strings sent on the wire via .value and
model_dump().
"""

import json
from datetime import UTC, datetime
from decimal import Decimal

from nalogo.dto.income import (
    AtomDateTime,
    CancelCommentType,
    CancelRequest,
    IncomeClient,
    IncomeRequest,
    IncomeServiceItem,
    IncomeType,
    PaymentType,
)


class TestEnumValues:
    """Raw .value must round-trip the upstream-API strings exactly."""

    def test_income_type_values(self) -> None:
        assert IncomeType.FROM_INDIVIDUAL.value == "FROM_INDIVIDUAL"
        assert IncomeType.FROM_LEGAL_ENTITY.value == "FROM_LEGAL_ENTITY"
        assert IncomeType.FROM_FOREIGN_AGENCY.value == "FROM_FOREIGN_AGENCY"

    def test_payment_type_values(self) -> None:
        assert PaymentType.CASH.value == "CASH"
        assert PaymentType.ACCOUNT.value == "ACCOUNT"

    def test_cancel_comment_values(self) -> None:
        assert CancelCommentType.CANCEL.value == "Чек сформирован ошибочно"
        assert CancelCommentType.REFUND.value == "Возврат средств"


class TestEnumStringBehavior:
    """str() and equality behavior we explicitly rely on."""

    def test_str_subclass_equality(self) -> None:
        # Both (str, Enum) and StrEnum compare equal to the raw string.
        assert IncomeType.FROM_INDIVIDUAL == "FROM_INDIVIDUAL"
        assert PaymentType.CASH == "CASH"
        assert CancelCommentType.CANCEL == "Чек сформирован ошибочно"

    def test_json_dumps_uses_value(self) -> None:
        # json.dumps treats both str-Enum forms as the underlying string.
        assert json.dumps(IncomeType.FROM_INDIVIDUAL.value) == '"FROM_INDIVIDUAL"'
        assert json.dumps(PaymentType.CASH.value) == '"CASH"'


class TestDTOSerialization:
    """model_dump() on the request DTOs must produce the exact upstream payload."""

    def test_income_request_dump_includes_enum_value(self) -> None:
        item = IncomeServiceItem(
            name="Service",
            amount=Decimal("100"),
            quantity=Decimal("1"),
        )
        req = IncomeRequest(
            operation_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            request_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            services=[item],
            total_amount="100",
            client=IncomeClient(income_type=IncomeType.FROM_LEGAL_ENTITY),
            payment_type=PaymentType.ACCOUNT,
            ignore_max_total_income_restriction=False,
        )
        dumped = req.model_dump()
        assert dumped["paymentType"] == "ACCOUNT"
        assert dumped["client"]["incomeType"] == "FROM_LEGAL_ENTITY"

    def test_cancel_request_dump_includes_comment_value(self) -> None:
        req = CancelRequest(
            operation_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            request_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            comment=CancelCommentType.REFUND,
            receipt_uuid="abc",
        )
        dumped = req.model_dump()
        assert dumped["comment"] == "Возврат средств"
