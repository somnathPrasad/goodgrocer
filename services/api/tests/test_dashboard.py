from decimal import Decimal

from app.models.domain import Order
from app.services.dashboard import owner_summary


def order(data, number, status):
    return Order(
        order_number=number,
        customer_id=data["customer"].id,
        idempotency_key=number.lower(),
        request_hash="1" * 64,
        fulfilment_type="DELIVERY",
        status=status,
        payment_method="COD",
        subtotal=Decimal("100.25"),
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("100.25"),
        address_snapshot={"line1": "Market road"},
        customer_phone="+919876543210",
    )


def test_owner_summary_reports_actionable_orders_and_unavailable_catalogue(db, data):
    data["product"].available = False
    db.add_all(
        [
            order(data, "GG-DASHBOARD-PLACED", "PLACED"),
            order(data, "GG-DASHBOARD-ACCEPTED", "ACCEPTED"),
        ]
    )
    db.flush()

    summary = owner_summary(db)

    assert summary["awaiting_action"] == 1
    assert summary["today_orders"] == 2
    assert summary["unavailable_products"] == 1
    assert [item.order_number for item in summary["recent_orders"]] == [
        "GG-DASHBOARD-ACCEPTED",
        "GG-DASHBOARD-PLACED",
    ]
