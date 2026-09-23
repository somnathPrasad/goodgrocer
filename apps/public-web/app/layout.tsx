import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Goodgrocer · Your neighbourhood grocery store",
  description:
    "Order everyday groceries from your neighbourhood store with delivery and cash on delivery.",
};

function Brand() {
  return (
    <Link className="brand" href="/" aria-label="Goodgrocer home">
      <span className="brand-mark">g</span>
      <span>goodgrocer</span>
    </Link>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="header-inner">
            <Brand />
            <nav aria-label="Main navigation">
              <Link href="/#how-it-works">How it works</Link>
              <Link href="/privacy">Privacy</Link>
              <Link href="/delete-account">Delete account</Link>
            </nav>
          </div>
        </header>
        {children}
        <footer>
          <div className="footer-inner">
            <Brand />
            <p>
              Your neighbourhood grocery store, ready for the everyday list.
            </p>
            <div className="footer-links">
              <Link href="/privacy">Privacy policy</Link>
              <Link href="/delete-account">Delete account</Link>
              <a href="mailto:somnathprasad559@gmail.com">Contact</a>
            </div>
            <small>
              © {new Date().getFullYear()} Somnath Prasad · Goodgrocer
            </small>
          </div>
        </footer>
      </body>
    </html>
  );
}
