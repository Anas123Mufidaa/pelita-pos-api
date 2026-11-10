import pytest
from pydantic import ValidationError

from models import TransactionCreate


def test_transaction_create_validates_and_strips_input() -> None:
    transaction = TransactionCreate(
        product_id=1,
        quantity=2,
        cashier_name=" Kasir Pelita ",
    )

    assert transaction.cashier_name == "Kasir Pelita"


@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": 0, "quantity": 1, "cashier_name": "Kasir"},
        {"product_id": 1, "quantity": 0, "cashier_name": "Kasir"},
        {"product_id": 1, "quantity": 1, "cashier_name": " "},
    ],
)
def test_transaction_create_rejects_invalid_input(payload) -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**payload)
