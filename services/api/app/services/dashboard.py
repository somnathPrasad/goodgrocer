from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.models.domain import Order, Product
from app.schemas.domain import OrderOut


def owner_summary(db):
    today = datetime.combine(
        datetime.now(ZoneInfo("Asia/Kolkata")).date(),
        time.min,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )
    return {
        "awaiting_action": db.scalar(
            select(func.count()).select_from(Order).where(Order.status == "PLACED")
        ),
        "today_orders": db.scalar(
            select(func.count()).select_from(Order).where(Order.created_at >= today)
        ),
        "unavailable_products": db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.active.is_(True), Product.available.is_(False))
        ),
        "recent_orders": [
            OrderOut.model_validate(order)
            for order in db.scalars(select(Order).order_by(Order.id.desc()).limit(8))
        ],
    }
