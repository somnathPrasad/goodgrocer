# Goodgrocer product

## Product summary

Goodgrocer is a grocery ordering product for one physical Kirana store. The
store will serve customers in its local town through delivery and pickup.
Approximately 500 products are expected initially.

Android is the primary customer platform. Customers may browse without
authentication; authentication, when introduced, will use a phone number and
one-time password. A web administration portal will later allow the store owner
to manage products, availability, orders, and related store operations. A
native iOS application using Swift and SwiftUI is planned for a later phase.

## Product direction

The intended customer experience includes:

- product browsing, search, and categories;
- favourites and a cart;
- phone number and OTP authentication;
- saved addresses and checkout;
- cash on delivery, online UPI, and UPI on delivery;
- local delivery and store pickup;
- simple order tracking and reorder.

Products belong to categories and may have variants such as 500 g, 1 kg, and
5 kg. Each variant has its own price and availability. Inventory quantities do
not need to be tracked initially. The store owner manually controls product and
variant availability. A variant is orderable only when both its product and the
variant itself are available. Whether unavailable items remain visible to
customers has not been decided.

The currently agreed order statuses are:

- `PLACED`
- `ACCEPTED`
- `OUT_FOR_DELIVERY`
- `DELIVERED`
- `CANCELLED`

Status transitions and cancellation rules have not been decided.

Delivery is limited to the store's local town, and pickup will be supported.
The town, delivery boundaries, delivery fees, minimum order, and detailed
pickup policies have not been decided.

## Current scope

The current milestone creates the initial backend foundation: a FastAPI
service with a liveness endpoint, PostgreSQL development container,
environment-based database configuration, SQLAlchemy setup, and Alembic
migration environment.

It does not include:

- Android, iOS, or admin portal application code;
- authentication or OTP handling;
- products, search, favourites, cart, addresses, checkout, or orders;
- payment or UPI integrations;
- administration functionality;
- database schemas or migration revisions;
- shared product API contracts or generated clients;
- deployment infrastructure;
- formatting or continuous integration tooling.
