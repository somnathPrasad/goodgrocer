# Goodgrocer customer experience

This context defines customer-facing browsing and ordering language, including
catalogue continuity and first-release checkout choices.

## Language

**Browsing continuity**:
The customer continues to see the last loaded catalogue content while newer
content is being retrieved.
_Avoid_: blank refresh, blocking reload

**Browsing context**:
A customer's current catalogue view, including its query or category and the
loaded products associated with that view.
_Avoid_: one global product list

**Catalogue freshness**:
During an app session, previously loaded catalogue content may be shown
immediately while the store data refreshes in the background; a new session
starts with a fresh catalogue load.
_Avoid_: blocking every revisit until the network responds

**First-load placeholder**:
A screen-specific placeholder shown only when that screen has no loaded content
yet.
_Avoid_: using a full-screen placeholder for refreshes or actions

**Operation progress**:
A local progress indication for refreshing content or completing an action while
the current screen remains usable where possible.
_Avoid_: global loading state

**Authenticated continuity**:
Previously loaded favourites, orders, and addresses may remain visible during a
refresh, but are cleared immediately when the customer signs out.
_Avoid_: showing one customer's data after logout

**Customer**:
The Goodgrocer identity created when a person first authenticates with Google.
_Avoid_: Google account, user account

**Customer deletion**:
Permanent removal of a Customer's authentication identity, sessions, saved addresses, favourites, and other reusable personal data.
_Avoid_: sign-out, Google account deletion, order cancellation

**Deletion path**:
An independently accessible native or web experience in which a Customer authenticates with Google and explicitly confirms Customer deletion.
_Avoid_: support request, sign-out flow

**Deletion authorization**:
A freshly verified Google identity presented only to authorize Customer deletion without creating a new Customer.
_Avoid_: existing session alone, account lookup

**Deletion confirmation**:
The final informed Customer action that permanently authorizes deletion after its consequences and selected Google identity are shown.
_Avoid_: typed confirmation phrase, support approval

**Public website**:
Goodgrocer's customer-facing website for product information, store links, and account-support experiences such as the web Deletion path.
_Avoid_: web shop, owner portal

**Retained order record**:
An order snapshot kept independently of a deleted Customer only as needed for fulfilment, accounting, fraud prevention, or other disclosed legal obligations.
_Avoid_: active customer profile

**Pending order erasure**:
The temporary retention of an active order's delivery details after Customer deletion until that order is delivered, cancelled, or reaches the 30-day retention limit.
_Avoid_: indefinite order history retention

**Immediate product detail**:
Product detail begins with the matching cached catalogue product when available,
then reconciles with the current store response.
_Avoid_: blank detail while a known product is fetched again

**Refresh window**:
A browsing context is refreshed when active unless its last successful refresh
was within roughly one minute; an explicit customer refresh bypasses the window.
_Avoid_: refreshing on every tab selection

**Cash on delivery (COD)**:
The first-release payment method for a delivery order, collected by the store when the order arrives.
_Avoid_: cash at collection, UPI on delivery

**Store pickup**:
A later-release fulfilment option in which the customer collects an order from the store.
_Avoid_: first-release checkout option

## Relationships

- **Browsing continuity** applies to catalogue browsing and refreshes; it does
  not replace the first-load state when no content has been loaded yet.
- A **Browsing context** can be restored when the customer returns from a
  product or category view.
- **Catalogue freshness** permits cached content during a session but does not
  imply that prices or availability are permanent.
- A **First-load placeholder** is distinct from **Operation progress**.
- **Authenticated continuity** ends at logout.
- **Customer deletion** ends the **Customer** identity and every authenticated session permanently.
- On Android, **Customer deletion** also clears the local cart, checkout key, authenticated caches, deletion credentials, and navigation history; sign-out continues to preserve the cart.
- The native and web **Deletion paths** invoke the same immediate **Customer deletion** operation after separate authentication and confirmation experiences.
- Each **Deletion path** requires **Deletion authorization** and reports success when the Customer has already been deleted.
- Each **Deletion path** explains the consequences, obtains **Deletion authorization**, identifies the selected Google account, and then requires **Deletion confirmation**.
- In the native **Deletion path**, **Deletion authorization** must identify the currently authenticated **Customer**; selecting a different Google account leaves both Customers unchanged.
- Authenticating again after **Customer deletion** creates a new **Customer** without restoring deleted data or prior order access.
- The web **Deletion path** belongs to the **Public website**, which remains separate from the owner portal and does not offer catalogue browsing or ordering.
- **Customer deletion** does not cancel an active order; active and historical orders continue as **Retained order records**.
- A **Retained order record** is detached from the deleted **Customer** and retains non-personal commercial facts.
- A **Retained order record** may record when its Customer was deleted, but does not retain a hidden or anonymized Customer identity.
- Customer deletion removes any payment-attempt records associated with retained orders in the cash-on-delivery release; payment method and payment state remain commercial facts.
- Terminal **Retained order records** have their delivery address, coordinates, recipient name, and contact phone erased immediately.
- **Pending order erasure** keeps those delivery details for an active order only until it becomes delivered, cancelled, or reaches 30 days after Customer deletion, then erases them automatically.
- **Immediate product detail** is unavailable only when the product has not
  already been loaded in the current session.
- A **Refresh window** limits background traffic without preventing explicit
  refresh.
- **Cash on delivery (COD)** applies to first-release delivery orders; **Store pickup** is unavailable in that release.
- Checkout shows the first-release **Cash on delivery (COD)** method and delivery fulfilment only.
- Existing orders keep their recorded fulfilment and payment method; reordering their items follows the current checkout choices.

## Example dialogue

> **Dev:** "What should a customer see while the catalogue refreshes?"
> **Domain expert:** "Keep the last loaded products visible and indicate that
> an update is in progress; do not replace the store with a blank loading
> screen."
>
> **Dev:** "When they come back from a product, do we start the catalogue over?"
> **Domain expert:** "No. Restore the same browsing context, including the
> search or category they were using."
>
> **Dev:** "Can that content be shown immediately if it may be slightly old?"
> **Domain expert:** "Yes, for this session—refresh it in the background so
> prices and availability catch up."
>
> **Dev:** "Should a refresh replace the whole screen with a placeholder?"
> **Domain expert:** "No. Keep the current screen usable and show progress only
> for the operation being performed."
>
> **Dev:** "Can saved data remain visible while it refreshes?"
> **Domain expert:** "Yes, but signing out must clear it immediately so another
> customer cannot see it."
>
> **Dev:** "When opening a product we already displayed, should detail wait for
> the network?"
> **Domain expert:** "No. Show the known product immediately and update it when
> the store response arrives."
>
> **Dev:** "Should switching tabs repeatedly call the API each time?"
> **Domain expert:** "No. Refresh active content after a short window, but let
> an explicit refresh happen immediately."
>
> **Dev:** "Does deleting a Customer cancel an order that is out for delivery?"
> **Domain expert:** "No. Remove the Customer identity and reusable personal data; the store completes the order from its retained snapshot."
>
> **Dev:** "Can the customer collect an order and pay cash at the store in the first release?"
> **Domain expert:** "No. The first release accepts delivery orders paid in cash on delivery."

## Flagged ambiguities

- "Loading screen" can mean either the first-load placeholder for a screen or
  a progress indication during refresh. The product decision is to use a
  placeholder only when that screen has no loaded content.
- "COD" previously also labeled cash at pickup. For the first release it means
  cash collected on delivery; pickup is unavailable for new orders.
- "Account deletion" means **Customer deletion** within Goodgrocer. It does not delete the person's Google account or cancel their orders.
- "Customer web" does not mean a web shop in the first release; the **Public website** provides information, store links, and account support only.
