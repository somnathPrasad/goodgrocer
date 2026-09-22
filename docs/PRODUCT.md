# Goodgrocer product

## V1 scope

One physical Kirana store, approximately 500 products, a native Android customer
app, a native Android owner app and the retained store-owner web portal share one backend. The
customer Android app opens with Google sign-in. After sign-in, customers can browse,
search and use a persistent local cart. Google sign-in also authenticates checkout,
saved addresses, account favourites and orders. A contact phone is collected from the
delivery address; it is not an account identifier. In the first release, customers
place delivery orders with cash on delivery (COD), track status, and reorder at
current prices. Store pickup, UPI on delivery and online UPI remain implemented
but are hidden from checkout and rejected by the API for this release.
Existing orders using those methods remain visible and can complete their
recorded owner and customer workflows. Reordering copies items into the cart;
the new checkout uses the first-release delivery and COD rule.

## Catalogue

Products have a brand, description, primary image, active and available flags,
and **multiple flat categories**. Categories have images and display order.
Variants have flexible labels (500 g, 2 L, Family Pack, Regular), display order,
MRP and selling price (decimal rupees), active and available flags.
`0 <= selling_price <= mrp`. No unit taxonomy or inventory quantities.
An item is orderable only if product.active AND product.available AND
variant.active AND variant.available. Inactive items are hidden; unavailable
active items remain visible with an unavailable label. Admin controls availability.

## Orders and checkout

The backend validates all quantities, availability and current prices and issues
an expiring quote. Order creation checks it again; changes require a fresh quote.
Orders retain item names/prices and delivery address snapshots. Payment state
(PENDING, PAID, FAILED, REFUNDED) is independent of order state.

Exact order states and transitions:

- PLACED → ACCEPTED or CANCELLED
- ACCEPTED → OUT_FOR_DELIVERY or CANCELLED
- OUT_FOR_DELIVERY → DELIVERED or CANCELLED
- DELIVERED and CANCELLED are terminal

Existing pickup orders additionally permit ACCEPTED → DELIVERED when collected. No PACKING.
Cancellation requires a reason. Cancellation of a paid online order is blocked
until a production refund integration exists. COD is marked PAID by the owner when
cash is received, independently of delivery status. The first release accepts
delivery and COD only; pickup and other payment methods are disabled.

Delivery serviceability is decided manually by the owner, who may cancel an
unserviceable order. No maps, geofences, routing or automatic address validation.
Delivery fee is configurable (default zero), with no minimum order or discounts.

## Owner apps

One admin account type; secure bootstrap, password login and expiring sessions.
The native Android owner app is the primary owner interface; the web portal remains available.
Dashboard, brands, categories (ordering/images), product search/filter/edit,
multi-category assignment, variant pricing/order/availability and order workflow.
Images are uploaded with type/size validation; database holds references only.

## Exclusions and future direction

No iOS, customer web shop, tenants/multi-store, subcategories, inventory counts,
coupons/promotions/combos, reviews/chat, drivers/tracking, staff roles/RBAC,
loyalty, order notifications, or distributed infrastructure. Future native iOS
and multi-store design remain future considerations; no store_id is added now.
Google OAuth client configuration, online UPI, deployment and backups require operator configuration.
