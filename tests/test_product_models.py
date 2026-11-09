import pytest
from pydantic import ValidationError

from models import ProductCreate


def test_product_create_strips_whitespace() -> None:
    product = ProductCreate(
        sku=" KOPI-001 ",
        nama=" Americano ",
        kategori=" Minuman ",
        harga=18000,
        stok=10,
    )

    assert product.sku == "KOPI-001"
    assert product.nama == "Americano"
    assert product.kategori == "Minuman"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sku", " "),
        ("nama", ""),
        ("kategori", " "),
        ("harga", -1),
        ("stok", -1),
    ],
)
def test_product_create_rejects_invalid_values(field, value) -> None:
    payload = {
        "sku": "KOPI-001",
        "nama": "Americano",
        "kategori": "Minuman",
        "harga": 18000,
        "stok": 10,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        ProductCreate(**payload)
