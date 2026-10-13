# WhatsApp login: operator setup guide

Checked on 2026-10-13. This is a proposed setup guide, not an accepted
architecture decision. Customer login remains Google-based until implementation
and production readiness are confirmed.

## Feasibility

Goodgrocer can technically authenticate a phone number by sending a WhatsApp
one-time code and verifying it in FastAPI. WhatsApp is the delivery channel;
Goodgrocer issues its own session. [Meta authentication overview](https://whatsappbusiness.com/products/conversation-categories/authentication/)

Not incorporating a company is different from lacking all business evidence.
A sole-proprietor store has a potential verification path: incorporation is
only one document type in the provider's India list, alongside shop certificates,
business licences, GST certificates and business bank statements. This is an
inference from the alternatives, not a promise of approval. Confirm the actual
documents accepted in the account's verification screen. Personal identity
documents alone must not be assumed to establish the business.
[360dialog verification documentation](https://docs.360dialog.com/docs/resources/meta-business-verification)

360dialog documents authentication eligibility as a completed Meta scaling path
and at least a 2,000 daily messaging limit. This is capacity, not mandatory daily
traffic. Direct Meta's detailed authentication documentation was inaccessible
during this investigation, so confirm the rule against the actual WABA before
committing to a replacement login. API onboarding or a successful sample message
does not prove production authentication eligibility.
[360dialog authentication requirements](https://docs.360dialog.com/partner/messaging/template-messages/authentication-templates)

## Your setup steps

1. **Establish the business identity and documentary path.** Decide which real
   store/operator owns Goodgrocer. Gather existing business-name and address
   evidence. Ask Meta support or a prospective official provider which documents
   qualify for this Indian sole proprietorship and whether authentication
   templates can be enabled. Do this before paying for a subscription or changing
   the sender number. If no evidence exists, establish an accepted business
   documentation path first. Udyam is one registration route to investigate;
   its official portal is free and specifies PAN/GSTIN as applicable, but its
   existence does not guarantee Meta acceptance. Do not incorporate a company
   solely on an unsupported assumption that WhatsApp requires it.
   [Official Udyam portal](https://udyamregistration.gov.in/)

2. **Prepare the public website.** Deploy Goodgrocer's existing public website
   over HTTPS. Supply the accurate operator/store name, address, support contact
   and relationship between the legal operator and the Goodgrocer brand. The
   current privacy page identifies Somnath Prasad; reconcile that with the
   selected business identity. I will update the privacy and account-deletion
   code for the new login. Review and publish those changes before launch.
   WhatsApp requires accurate profile information and a published privacy policy.
   [WhatsApp policy](https://whatsappbusiness.com/policy/)

3. **Create or reuse an owner-controlled Meta business portfolio.** Use your
   genuine Facebook account, enable two-factor authentication, and retain full
   control of the business assets. Enter truthful business details matching the
   documents. Use the business verification option in Business Settings/Security
   Centre when available. Complete the offered connection-confirmation process.
   [Meta verification help](https://www.facebook.com/business/help/2058515294227817)

4. **Choose direct Cloud API or an official provider.** Direct Meta Cloud API is
   my proposed starting route because our backend already has a WhatsApp webhook
   receiver. A provider may assist onboarding, but require explicit confirmation
   of India OTP support, document acceptance, account ownership and fees. It
   cannot simply bypass Meta eligibility. In particular, 360dialog currently
   states new partner-led verification submissions are paused; do not rely on
   that route without a confirmed change.
   [360dialog pause notice](https://docs.360dialog.com/docs/resources/meta-business-verification/plbv)

5. **Create the Meta developer app and WhatsApp assets.** For direct integration,
   add the WhatsApp use case/product, connect the intended portfolio and create
   or select its WhatsApp Business Account (WABA). Save the app ID, portfolio ID
   and WABA ID. Meta's test sender is useful for connectivity only.
   [Meta-owned Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/collection/wlk6lh4/whatsapp-cloud-api)

6. **Onboard a store-controlled sender number.** Prefer a dedicated number that
   can receive Meta's registration SMS or voice call. Complete ownership
   verification and sender registration, set its two-step-verification PIN, and
   configure its business profile/display name. Record the Phone Number ID.
   If reusing an existing WhatsApp number, confirm the supported migration or
   coexistence flow first; do not delete its account as a preliminary step.

7. **Confirm authentication eligibility in WhatsApp Manager.** Check account
   restrictions, verification/scaling status and messaging capacity. If
   authentication creation is unavailable, resolve the eligibility issue with
   Meta/provider. Do not disguise login codes as utility or marketing messages.
   See the authentication requirements linked above.

8. **Configure billing and create an approved authentication template.** Add the
   payment method offered for the WABA. Use a name such as
   `goodgrocer_login_code`, the Authentication category and Copy Code button.
   Start with English and add needed languages separately. My proposed code
   lifetime is five minutes; keep any template expiry notice aligned with the
   backend. Wait for approval. One-tap can be added later using the app package
   `com.goodgrocer.app` and production signing hash supplied by me.
   [Copy-code and one-tap documentation](https://www.twilio.com/docs/content/whatsappauthentication)

9. **Prepare production API credentials.** Create a system user with access to
   the app/WABA and an appropriate production access token. Sending uses
   `whatsapp_business_messaging`; template/account management uses
   `whatsapp_business_management`. Store the token and Meta App Secret only in
   the backend deployment's secret settings. Temporary dashboard tokens are
   unsuitable for production. Share non-secret IDs and template information
   with me; do not paste credentials into chat or Git. See Meta's collection above.

10. **Configure the existing webhook with me.** Deploy the API over HTTPS. In
    Meta, set callback URL
    `https://YOUR_API_HOST/api/v1/webhooks/whatsapp`, verify it using the chosen
    webhook Verify Token, subscribe to `messages`, and ensure the app is
    subscribed to the WABA. Backend configuration and the existing cleanup
    command are documented in [PRODUCTION.md](../PRODUCTION.md#whatsapp-webhook).
    The receiver currently captures events; it does not send or verify OTPs.

11. **Prove real production delivery.** With my API/Postman assistance, send the
    approved authentication template from the real sender to consenting Indian
    test numbers. Confirm receipt on their primary phones and delivery status;
    a successful send-request response alone is insufficient. Test resends and
    offline recipients. Budget by delivered authentication messages, including
    resends, plus any provider fees and applicable taxes. Obtain the current India
    price from the account/rate card rather than treating a quoted estimate as fixed.
    [Meta pricing](https://whatsappbusiness.com/products/platform-pricing/)

12. **Complete the release setup with me.** I will implement backend challenges,
    expiry/attempt/resend controls, Android phone login, account-deletion flows,
    tests and updated product/architecture decisions. If existing Google accounts
    have real users, linking must prove both the existing account and new phone;
    address contact numbers are not verified account ownership. Decide whether
    customers without usable WhatsApp need another login route before launch.
    Update the privacy disclosures and Play Console data-safety answers to match
    the released behavior, then test the signed release before switching login.

## Provider-specific caution

Twilio Verify currently documents SMS fallback for WhatsApp OTP attempts to India.
Do not buy it assuming it supplies the requested WhatsApp-only India login.
This limitation is specific to that product, not a claim about every WhatsApp API.
[Twilio Verify templates](https://www.twilio.com/docs/verify/verification-templates)

## Ready-to-implement handoff

Non-secret details: accepted verification outcome, selected integration route,
Meta app ID, WABA ID, Phone Number ID, sender number, approved authentication
template name/languages, API and website URLs, and whether real Google accounts
need migration. Credentials belong in deployment secrets. The decisive external
proof is a real delivered authentication message from the production sender.
