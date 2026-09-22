# Customer Android UX handoff

Prepared 2026-09-22 after reviewing the running customer app on a connected
physical Android device (CPH2467, 1080 × 2400). This is an implementation
handoff for a new session. No app code or user data was changed during the review.

## Scope and constraints

- Customer app: `apps/android/` (Kotlin, Jetpack Compose, Material 3).
- Keep the first-release delivery and cash-on-delivery scope in
  `docs/PRODUCT.md`. Do not expose pickup or UPI checkout options.
- Preserve the order-status vocabulary and backend API boundary in
  `docs/ARCHITECTURE.md`.
- Device review covered Home, Search and no results, category, product, basket,
  checkout and quote, address list, map picker, manual address form, Saved,
  Orders, order detail, and Account. The device was already signed in, so the
  entry screen was reviewed from code only. No order was placed, and no saved
  address or account data was modified.

## Work in priority order

### 1. Show the complete delivery choice before order placement

**Observed:** Checkout and final quote show only recipient, first address line,
and city. The customer cannot verify the delivery phone, remaining address
details, or postal code at the decision point.

**Change:** Show the selected address in full, including recipient, phone,
address lines, locality/landmark when present, city, state, and postal code.
Keep the serviceability warning; the owner still makes that decision. Ensure
the full details remain visible when the quote is shown.

**Done when:** A customer can verify the delivery address and phone on the
final review screen before tapping Place order. No private address details
are added to logs or analytics.

Code: `apps/android/app/src/main/java/com/goodgrocer/app/ui/OrderScreens.kt`
(`CheckoutScreen`, around line 84).

### 2. Give search-specific empty and error states

**Observed:** A completed no-match search displays “Nothing here yet” and
“Try another search, or refresh to reconnect.” This implies a connection
problem even though the request succeeded. Search can also open with an empty
field while showing products left from another catalogue view.

**Change:** Separate no matches from network failure. In no matches, echo the
query and offer Clear search. Use reconnect/retry copy only after a request
fails. Make the initial Search state explicit (for example, show all products
with a heading or an intentional search prompt), and keep the visible query
consistent with the displayed results.

**Done when:** No-match, failed request, and initial Search each show accurate
copy and recovery actions. Moving between Home, category, and Search does not
leave a query/result mismatch.

Code: `apps/android/app/src/main/java/com/goodgrocer/app/ui/CatalogueScreens.kt`
(`CatalogueScreen`, around lines 73 and 173–245) and `ShopViewModel.kt`
(`browse`, around line 137).

### 3. Remove or implement Account dead ends

**Observed:** Help & Support was tapped on the device and did nothing. Store
Information and About Goodgrocer are also rendered as tappable cards with
chevrons but have empty callbacks.

**Change:** Give each visible row a useful destination/action, or remove the
row until its content exists. Avoid adding speculative product features.

**Done when:** Every visible Account card responds as its label suggests.

Code: `apps/android/app/src/main/java/com/goodgrocer/app/ui/AccountScreens.kt`
(around lines 223–242).

### 4. Improve the first shopping viewport and product action placement

**Observed:** The Home hero and aisle row push product prices and Add buttons
below the first viewport. Product detail uses a large image and repeats the
selected price below the priced variant choices, leaving Add near the bottom.

**Change:** Reduce the repeat-visit hero height so shopping actions appear
sooner. On product detail, group the selected variant, its price, and quantity
control; remove redundant price presentation. Check smaller screens and
larger font settings before choosing a persistent product action bar.

**Done when:** Search/aisles and at least one actionable product are easy to
reach on Home, and the selected size and Add control remain visually connected
on product detail.

Code: `apps/android/app/src/main/java/com/goodgrocer/app/ui/CatalogueScreens.kt`
(Home around lines 99–162; product detail around lines 279–379).

### 5. Limit the floating basket bar to shopping screens

**Observed:** The View basket bar appears on Addresses, the address editor,
Account, Orders, and order detail, taking space from those tasks.

**Change:** Show it on Home, Search, categories, products, and Saved where
shopping context makes it useful. Keep normal basket access through the
shopping flow.

**Done when:** Account, address, checkout, and order screens have no floating
basket bar; shopping screens still provide an obvious basket entry point.

Code: `apps/android/app/src/main/java/com/goodgrocer/app/ui/ShopApp.kt`
(around lines 111–136).

### 6. Polish catalogue content and customer-facing labels

- Multi-variant product cards show one variant's price alongside “Choose
  size.” Use “From ₹…” or another truthful price label. See `Design.kt`
  `ProductCard` around line 245.
- Render order payment and fulfilment as customer language rather than raw
  values such as `DELIVERY · COD` and `Payment: PAID`. Preserve API/status
  values internally. See `OrderScreens.kt` `OrderScreen` around line 345.
- Remove duplicated Account shortcuts or menu entries; replace the generic
  member/verified panel with useful account information only if available.
  See `AccountScreens.kt` around lines 120–206.
- Mark required address fields, give inline phone validation, and explain why
  Save is disabled. Improve the map center pin's visibility. See
  `AccountScreens.kt` `AddressEditor` around line 491 and `MapPinPicker.kt`
  around line 131.
- On basket, verify that image, quantity controls, and Remove remain readable
  with long product names and larger text. See `CatalogueScreens.kt` around
  line 401.

## Verification in the next session

1. Rebuild and run the customer app on a physical device or emulator with
   seeded products and a signed-in test account.
2. Walk Home → Search (initial, no matches, offline error) → category →
   product variants → basket → checkout → quote. Stop before Place order unless
   an explicit test-order setup is available.
3. Inspect saved address selection and final quote with a test address; verify
   its full details and phone are shown without editing live customer data.
4. Open every visible Account row and confirm it responds. Review Orders and
   order detail with existing test orders.
5. Repeat key screens at a smaller display width and Android font scale 1.3×
   or greater, especially the five-item navigation bar, product cards, basket
   row, checkout, and address form.

The code-only review is in the prior conversation. Device screenshots were
captured during that session for inspection but are intentionally not committed
because they contain account, order, and address details.
