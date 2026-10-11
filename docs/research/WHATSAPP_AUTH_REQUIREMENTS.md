# WhatsApp OTP requirements investigation

Checked on 2026-10-10. This is research, not an accepted architecture decision.

## Confirmed from primary sources

- WhatsApp Business Platform supports OTP authentication, including account
  creation and recovery. Its native features include one-tap, autofill and
  zero-tap authentication. This is a delivery channel for Goodgrocer's login
  challenge; the backend still needs to validate the code and issue its own
  session. [WhatsApp authentication messages](https://whatsappbusiness.com/products/conversation-categories/authentication/)
- Meta's official Cloud API collection lists a Meta business portfolio, WhatsApp
  Business Account (WABA) and business phone number as required assets. It also
  explains API access tokens, including system-user tokens for production use.
  Direct Cloud API integration is available; a messaging provider can instead
  handle its onboarding and integration. [Meta Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/collection/wlk6lh4/whatsapp-cloud-api)
- Business-initiated messages require an approved template used for its
  designated purpose. A login implementation should use the authentication
  category, and confirm that the actual WABA can create and send that category
  before replacing the existing login. [WhatsApp Business Messaging Policy](https://whatsappbusiness.com/policy/),
  [Authentication category](https://whatsappbusiness.com/products/conversation-categories/authentication/)
- The business must obtain the recipient's number and opt-in permission. Make
  the login action explicitly request an OTP on WhatsApp; do not treat that
  action as consent to marketing. Maintain an accurate business profile,
  support contact and published privacy policy. [Messaging Policy, sections 1–3 and opt-in guidance](https://whatsappbusiness.com/policy/)
- Meta charges per delivered message according to category and recipient
  market, with authentication volume tiers. Budget for resends as well as
  successful logins, and obtain any provider fees separately. The current India
  rate was not verified in the dynamic rate selector, so this note deliberately
  does not quote a rupee price. [Official pricing](https://whatsappbusiness.com/products/platform-pricing/)

## Preflight items and limits of this investigation

- **API access is not proof of authentication-template eligibility.** Meta's
  detailed authentication-template and messaging-limit docs could not be fetched
  in this session (rate limiting/access errors). A claim that every new account
  must first send 2,000 messages in 30 days is therefore not established here.
  Distinguish a daily messaging-limit tier from historical usage required by a
  particular scaling path. Check actual eligibility in WhatsApp Manager or with
  the chosen provider, then create an approved authentication template and test
  delivery. [Meta authentication docs, inaccessible in this investigation](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/)
- **Business verification is separate from incorporating a company.** No
  accessible primary source in this investigation establishes that a private
  limited company is mandatory, or confirms which Indian sole-proprietor
  documents Meta currently accepts. Do not promise approval for an unregistered
  individual. Ask Meta/provider whether the store's existing legal name,
  registration/tax documents, address and contact evidence qualify before
  spending time on incorporation solely for this integration. The relevant
  business-verification help page redirected to login.
  [Meta business verification help](https://www.facebook.com/business/help/2058515294227817)
- Verify ownership and onboarding requirements for the sender number. Do not
  assume a number already used in the WhatsApp Business app can be moved or used
  simultaneously without checking the selected provider's supported onboarding
  and coexistence flow. Coexistence eligibility was not verified from primary
  documentation in this session.
- Prove production template delivery to real customer test numbers before
  removing Google sign-in. Consider an SMS fallback so customers without
  WhatsApp, internet access or timely message delivery can still authenticate.
  This is an implementation recommendation, not a WhatsApp requirement.

## Suggested account proof before implementation

1. Create/select the business portfolio and WABA, choose direct Cloud API or a
   provider, and onboard a business-controlled sender number.
2. Confirm the store's verification path and authentication-category eligibility.
3. Obtain an approved authentication template and a billing/payment setup.
4. Send a production OTP to a real test recipient and inspect delivery outcomes.
5. Only then schedule the customer identity, backend OTP, Android login and
   public-web account-deletion changes.
