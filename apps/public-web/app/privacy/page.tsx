export const metadata = { title: "Privacy policy · Goodgrocer" };

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <p className="eyebrow">GOODGROCER</p>
      <h1>Privacy policy</h1>
      <p className="updated">Last updated: 23 September 2026</p>
      <p>
        Goodgrocer is operated by Somnath Prasad. This policy explains how the
        Goodgrocer Android app and public website handle information.
      </p>
      <h2>Information we handle</h2>
      <ul>
        <li>
          Your Google account identifier is used to create and authenticate your
          Goodgrocer account.
        </li>
        <li>
          Saved delivery addresses include recipient name, phone number, address
          text and optional map coordinates.
        </li>
        <li>
          Favourites, orders, order items and status history support shopping
          and fulfilment.
        </li>
        <li>
          The app keeps the basket and session information on your device.
        </li>
      </ul>
      <h2>How information is used</h2>
      <p>
        We use this information to authenticate you, save requested preferences,
        prepare and fulfil orders, provide order history, prevent abuse and
        operate the service. We do not sell personal information.
      </p>
      <h2>Google services</h2>
      <p>
        Goodgrocer uses Google Sign-In for authentication and Google Maps
        services when you choose a delivery location. Google processes
        information under its own terms and policies.
      </p>
      <h2>Account deletion and retention</h2>
      <p>
        You can delete your account from the Android Account screen or the
        public
        <a href="/delete-account"> account deletion page</a>. Deletion removes
        your Goodgrocer identity, sessions, saved addresses and favourites. It
        does not delete your Google account or cancel an order.
      </p>
      <p>
        Personal delivery details on delivered or cancelled orders are erased
        immediately. An active order keeps the details needed for fulfilment
        until it is delivered, cancelled or reaches 30 days after deletion,
        whichever is first. Detached commercial order facts such as items,
        prices, status and payment state may remain.
      </p>
      <p>
        Deleting inside Android also clears the basket and other Goodgrocer data
        stored by the app on that device. The website cannot erase a basket held
        only on another device; clear the app&apos;s storage or uninstall it to
        remove that local data.
      </p>
      <h2>Security</h2>
      <p>
        Production traffic is transmitted over HTTPS. Authentication sessions
        are stored as hashes on the server, and Android session material is
        encrypted using Android Keystore.
      </p>
      <h2>Contact</h2>
      <p>
        For privacy questions, contact Somnath Prasad at{" "}
        <a href="mailto:support@goodgrocer.site">
          support@goodgrocer.site
        </a>
        .
      </p>
    </main>
  );
}
