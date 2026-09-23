const playStoreUrl = process.env.NEXT_PUBLIC_PLAY_STORE_URL;

function PlayStoreAction() {
  if (!playStoreUrl) {
    return (
      <span className="store-badge disabled">Coming soon on Google Play</span>
    );
  }
  return (
    <a className="store-badge" href={playStoreUrl} rel="noreferrer">
      <span>GET IT ON</span>
      <strong>Google Play</strong>
    </a>
  );
}

const steps = [
  [
    "01",
    "Browse your essentials",
    "Find groceries, sizes and current store availability.",
  ],
  [
    "02",
    "Build your basket",
    "Keep your everyday list on your phone and review current prices.",
  ],
  [
    "03",
    "Choose delivery",
    "Save an address or place the pin at your delivery entrance.",
  ],
  [
    "04",
    "Pay on delivery",
    "Place the order with cash on delivery. The store confirms serviceability.",
  ],
];

export default function Home() {
  return (
    <main>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">YOUR LOCAL STORE · ON ANDROID</p>
          <h1>
            Fresh finds,
            <br />
            right around the corner.
          </h1>
          <p className="lede">
            Browse the neighbourhood grocery shelf, keep your everyday basket,
            and order for delivery with cash on delivery.
          </p>
          <div className="hero-actions">
            <PlayStoreAction />
            <a className="text-link" href="#how-it-works">
              See how it works ↓
            </a>
          </div>
          <div className="hero-notes" aria-label="Goodgrocer highlights">
            <span>Local catalogue</span>
            <span>Current prices</span>
            <span>Cash on delivery</span>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sun" />
          <div className="leaf leaf-one" />
          <div className="leaf leaf-two" />
          <div className="phone">
            <div className="phone-top">
              <span className="mini-mark">g</span>
              <b>Good morning</b>
            </div>
            <div className="search-pill">What are you looking for?</div>
            <div className="aisle-title">
              <b>Everyday favourites</b>
              <span>See all</span>
            </div>
            <div className="product-grid">
              <div className="product-card">
                <span>🍅</span>
                <b>Tomatoes</b>
                <small>Fresh produce</small>
              </div>
              <div className="product-card">
                <span>🥛</span>
                <b>Fresh milk</b>
                <small>Dairy & breakfast</small>
              </div>
              <div className="product-card">
                <span>🍚</span>
                <b>Basmati rice</b>
                <small>Pantry essentials</small>
              </div>
              <div className="product-card">
                <span>🍌</span>
                <b>Bananas</b>
                <small>Fresh produce</small>
              </div>
            </div>
            <div className="basket-bar">
              <span>3 items</span>
              <b>View basket →</b>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="how-it-works">
        <p className="eyebrow">A SIMPLE EVERYDAY ORDER</p>
        <h2>From the store shelf to your doorstep.</h2>
        <div className="steps">
          {steps.map(([number, title, detail]) => (
            <article className="step" key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="split-section">
        <div>
          <p className="eyebrow light">MADE FOR THE NEIGHBOURHOOD</p>
          <h2>All the useful parts of your local shop, close at hand.</h2>
        </div>
        <div className="benefit-list">
          <article>
            <span>♡</span>
            <div>
              <h3>Save your regulars</h3>
              <p>Keep favourite products ready for the next list.</p>
            </div>
          </article>
          <article>
            <span>⌖</span>
            <div>
              <h3>Remember delivery addresses</h3>
              <p>
                Save addresses and choose a precise delivery pin when needed.
              </p>
            </div>
          </article>
          <article>
            <span>↻</span>
            <div>
              <h3>Track and reorder</h3>
              <p>Follow order status and rebuild a basket at current prices.</p>
            </div>
          </article>
        </div>
      </section>

      <section className="section delivery-section">
        <div>
          <p className="eyebrow">FIRST RELEASE, KEPT SIMPLE</p>
          <h2>Delivery with cash on delivery.</h2>
          <p>
            Goodgrocer currently accepts delivery orders paid in cash when they
            arrive. The store reviews each address and confirms whether it can
            be served.
          </p>
        </div>
        <div className="delivery-card">
          <span className="delivery-icon">⌂</span>
          <h3>Your address, reviewed by your store</h3>
          <p>
            A map pin helps describe the location. It does not guarantee
            serviceability.
          </p>
          <PlayStoreAction />
        </div>
      </section>
    </main>
  );
}
