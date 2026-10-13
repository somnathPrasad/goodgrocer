# WhatsApp OTP requirements investigation

Checked on 2026-10-13. This is research, not an accepted architecture decision.
The non-code setup checklist is in `WHATSAPP_LOGIN_SETUP.md`.

## Feasibility for Goodgrocer

WhatsApp supports account authentication with OTPs. This replaces the delivery
channel for a login challenge; Goodgrocer's backend still validates the challenge
and issues its own customer session. [Meta authentication messages](https://whatsappbusiness.com/products/conversation-categories/authentication/)

**Not incorporated as a company is different from having no verifiable business
identity.** The accessible sources do not establish that an Indian private
limited company is mandatory. There is a plausible route for a documented store
or sole proprietor, but we cannot promise approval for an individual with no
business evidence. Confirm the store's legal-name and address documents before
spending money or replacing Google login.

360dialog's current country-specific guidance lists Indian business licences,
shop-establishment certificates, GST certificates, PAN, Udyog Aadar (its wording),
business bank statements and utility bills among accepted document types. The
list does **not** mean any one document proves every requirement or that personal
PAN alone verifies a trading name. [360dialog business verification](https://docs.360dialog.com/docs/resources/meta-business-verification)

For classic verification, its separate guide distinguishes proof of legal
business name from proof of address or phone number. The latter must also identify
the legal business. Match details across documents, business settings and the
website; explain any relationship between the store's legal name and Goodgrocer.
[360dialog classic verification](https://docs.360dialog.com/docs/resources/meta-business-verification/classic-business-verification)

## Authentication eligibility is a separate gate

- 360dialog's current authentication documentation requires a completed Meta
  scaling path and a minimum daily messaging limit of **2,000** before accessing
  authentication templates. It names classic or partner-led verification as
  examples. This is provider documentation describing Meta requirements; the
  detailed Meta page itself was inaccessible during this check.
  [360dialog authentication requirements](https://docs.360dialog.com/docs/resources/authentication-messages)
- New portfolios begin at 250 unique recipients per rolling 24 hours outside
  customer-service windows. The documented routes to the 2,000 tier are business
  verification, or 2,000 delivered, high-quality template messages to unique
  recipients outside those windows within 30 days, followed by Meta review. The
  limit is shared across the portfolio. **A requirement to send 2,000 historical
  messages is not universal:** verification is another scaling route.
  [360dialog messaging limits](https://docs.360dialog.com/docs/resources/wabas/messaging-limits)
- Do not assume that the usage-based scaling route alone grants authentication
  eligibility. Bird's own service refuses authentication-template authoring when
  Meta reports `not_verified`. Provider rules and actual account capabilities
  must be checked separately. An approved draft is not proof of permission to
  deliver it. [Bird verification documentation](https://bird.com/en-it/docs/knowledge-base/whatsapp/business-verification)
- **Current provider caveat:** 360dialog's partner-led verification page says new
  submissions were temporarily paused from 2026-09-01 until further notice. That
  warning applies to its route, not every provider. Its process also requires
  business evidence and excludes personal IDs; a provider is not a blanket
  workaround for missing documents.
  [360dialog PLBV status and requirements](https://docs.360dialog.com/docs/resources/meta-business-verification/plbv)

The reliable launch proof is the actual portfolio capability, an approved
`AUTHENTICATION` template, and successful production delivery to real test
recipients. Neither a test sender, phone-ownership OTP nor a utility-template
approval establishes this.

## Template, policy and cost requirements

- Use an authentication template for login codes. Start with a **copy-code**
  button and manual entry. One-tap is Android-specific and additionally needs the
  app package name, signing-key hash and handshake implementation. Preset text
  supports optional security and expiry notices; URLs, media and emojis are not
  supported. Set delivery TTL no longer than code validity.
  [360dialog authentication documentation](https://docs.360dialog.com/docs/resources/authentication-messages)
- Obtain the recipient's number and permission to send the requested code. Make
  the login action explicitly request delivery through WhatsApp and keep
  marketing consent separate. Maintain accurate support details and a published
  privacy policy. Business-initiated messages require an approved template used
  for its designated purpose.
  [Meta messaging policy, updated 2026-09-23](https://whatsappbusiness.com/policy/)
- Meta charges by delivered message, recipient market and category. Authentication
  has volume tiers. Budget for delivered resend messages and any provider fees;
  verify the applicable India rate in the live rate card and billing account.
  No exact rupee rate is asserted here.
  [Meta pricing](https://whatsappbusiness.com/products/platform-pricing/)

## Unresolved points to check in the actual account

- Meta's current accepted India documents, including whether the proprietor's
  available certificate proves the legal name. Do not equate Udyam registration
  with guaranteed Meta acceptance.
- Sender ownership, SMS/voice verification, display-name review, billing, and
  production API credentials. Choose a dedicated business-controlled sender
  number unless the chosen onboarding flow explicitly supports coexistence.
- The actual account's authentication capability after verification and scaling.
- Production OTP delivery and webhook status, not merely an accepted API request.
- An alternative login route for customers without WhatsApp or usable delivery;
  this is an implementation recommendation, not a Meta requirement.

## Source access limitations

The [Meta authentication-template documentation](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/)
and its Markdown version were inaccessible. The [Meta verification overview](https://www.facebook.com/business/help/2058515294227817)
and [accepted-documents page](https://www.facebook.com/business/help/159334372093366)
redirected to a login/temporary-block screen. Consequently, detailed verification
and scaling claims above are explicitly attributed to first-party provider
documentation, not presented as independently read Meta policy. These findings
establish a conditional path, not a guarantee that this particular store will be
approved.
