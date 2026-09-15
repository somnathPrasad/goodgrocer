# Goodgrocer customer browsing

This context defines the customer-facing browsing language and the expected
continuity of catalogue content while a customer moves through the store.

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

**Immediate product detail**:
Product detail begins with the matching cached catalogue product when available,
then reconciles with the current store response.
_Avoid_: blank detail while a known product is fetched again

**Refresh window**:
A browsing context is refreshed when active unless its last successful refresh
was within roughly one minute; an explicit customer refresh bypasses the window.
_Avoid_: refreshing on every tab selection

## Relationships

- **Browsing continuity** applies to catalogue browsing and refreshes; it does
  not replace the first-load state when no content has been loaded yet.
- A **Browsing context** can be restored when the customer returns from a
  product or category view.
- **Catalogue freshness** permits cached content during a session but does not
  imply that prices or availability are permanent.
- A **First-load placeholder** is distinct from **Operation progress**.
- **Authenticated continuity** ends at logout.
- **Immediate product detail** is unavailable only when the product has not
  already been loaded in the current session.
- A **Refresh window** limits background traffic without preventing explicit
  refresh.

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

## Flagged ambiguities

- "Loading screen" can mean either the first-load placeholder for a screen or
  a progress indication during refresh. The product decision is to use a
  placeholder only when that screen has no loaded content.
