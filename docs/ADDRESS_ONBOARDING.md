# Customer address onboarding

Status: accepted on 2026-10-13 and implemented. Google sign-in remains unchanged.

## Confirmed choices

- Keep Google sign-in for customer authentication.
- Offer address onboarding to customers without saved addresses, including new
  customers and existing customers with no saved addresses.
- Check eligibility after Google sign-in and when restoring an existing session.
- The offer is shown at most once per Customer across devices, reinstalls and
  sign-outs. Skipping is allowed and takes the customer to Home.
- Displaying the offer consumes it, even if the customer closes the app without
  saving or skipping. Later app openings take the customer to Home.
- Saving an address during onboarding takes the customer to Home.
- Deleting the last saved address does not reset an already consumed offer.
- If saved addresses or onboarding history cannot be retrieved, allow entry to
  Home without consuming the offer. Check again on the next app opening; an
  unsuccessful lookup must not be treated as an empty address list.
- Customers can still add addresses through Account or checkout after skipping.
- A saved address remains delivery information, not verified account identity or
  proof of delivery serviceability.

## Implementation

- Read eligibility from the backend, then atomically claim an eligible offer
  immediately before opening the editor. A Customer-row lock prevents concurrent
  devices from receiving the offer twice. The eligibility read never mutates history.
- A committed claim with a lost response, or a process exit before rendering, can
  consume the offer without displaying it. This favors at-most-once prompting.
- Sign-in, restored sessions and returning from the background check eligibility;
  rotation preserves the current screen. A failed check takes the customer to Home.
- Open the existing editor directly. It retains manual entry and the map-first
  flow when Maps is configured. Skip and Back return to Home.
- Checkout continues to require an address independently of onboarding history.
- Address save success uses the write response, updating visible state and cache
  without requiring another network read. This prevents duplicate retry after a
  successful write followed by a failed list refresh.
- Run the new Alembic migration and deploy the backend before releasing Android.

The scope is customer Android onboarding. Existing public-web account deletion
and owner authentication are independent of this flow.
