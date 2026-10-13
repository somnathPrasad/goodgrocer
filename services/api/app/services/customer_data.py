from sqlalchemy import select

from app.core.errors import DomainError
from app.models.domain import Address, Customer, Favourite, Product
from app.services import catalogue


def _address_for_customer(db, customer_id, address_id):
    address = db.get(Address, address_id)
    if address is None or address.customer_id != customer_id:
        raise DomainError("NOT_FOUND", "Resource not found", 404)
    return address


def list_addresses(db, customer_id):
    return db.scalars(
        select(Address).where(Address.customer_id == customer_id).order_by(Address.id)
    ).all()


def address_onboarding(db, customer_id, *, claim=False):
    query = select(Customer).where(Customer.id == customer_id)
    if claim:
        # Refresh even if authentication already loaded this Customer: another
        # device may have consumed the offer while this request waited for its lock.
        query = query.with_for_update().execution_options(populate_existing=True)
    current = db.scalar(query)
    if current is None:
        raise DomainError("NOT_FOUND", "Resource not found", 404)
    has_address = db.scalar(select(Address.id).where(Address.customer_id == customer_id).limit(1))
    eligible = not current.address_onboarding_seen and has_address is None
    if claim and eligible:
        current.address_onboarding_seen = True
        db.flush()
    return {"eligible": eligible}


def create_address(db, customer_id, data):
    address = Address(customer_id=customer_id, **data.model_dump())
    db.add(address)
    db.flush()
    return address


def update_address(db, customer_id, address_id, data):
    address = _address_for_customer(db, customer_id, address_id)
    for key, value in data.model_dump().items():
        setattr(address, key, value)
    db.flush()
    return address


def delete_address(db, customer_id, address_id):
    db.delete(_address_for_customer(db, customer_id, address_id))
    db.flush()


def list_favourites(db, customer_id):
    products = db.scalars(
        select(Product)
        .join(Favourite)
        .where(Favourite.customer_id == customer_id, Product.active.is_(True))
        .order_by(Product.id)
    ).all()
    return [catalogue.product_out(product) for product in products]


def add_favourite(db, customer_id, product_id):
    catalogue.get_product(db, product_id)
    db.scalar(select(Customer).where(Customer.id == customer_id).with_for_update())
    if not db.get(Favourite, (customer_id, product_id)):
        db.add(Favourite(customer_id=customer_id, product_id=product_id))
    db.flush()


def remove_favourite(db, customer_id, product_id):
    favourite = db.get(Favourite, (customer_id, product_id))
    if favourite:
        db.delete(favourite)
        db.flush()
