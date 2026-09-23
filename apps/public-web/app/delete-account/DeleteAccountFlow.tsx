"use client";

import Script from "next/script";
import { useCallback, useEffect, useRef, useState } from "react";

const clientId = process.env.NEXT_PUBLIC_GOOGLE_WEB_CLIENT_ID ?? "";

function emailFromToken(token: string): string {
  try {
    const encoded = token
      .split(".")[1]
      .replaceAll("-", "+")
      .replaceAll("_", "/");
    const payload = JSON.parse(atob(encoded)) as { email?: unknown };
    return typeof payload.email === "string"
      ? payload.email
      : "Selected Google account";
  } catch {
    return "Selected Google account";
  }
}

export default function DeleteAccountFlow() {
  const googleButton = useRef<HTMLDivElement>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [credential, setCredential] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [complete, setComplete] = useState(false);

  const renderGoogleButton = useCallback(() => {
    if (!scriptReady || !clientId || !googleButton.current || !window.google)
      return;
    googleButton.current.replaceChildren();
    window.google.accounts.id.initialize({
      client_id: clientId,
      auto_select: false,
      cancel_on_tap_outside: true,
      callback: ({ credential: token }) => {
        setError("");
        setCredential(token);
        setEmail(emailFromToken(token));
      },
    });
    window.google.accounts.id.renderButton(googleButton.current, {
      type: "standard",
      theme: "outline",
      size: "large",
      text: "continue_with",
      shape: "pill",
      width: Math.min(360, googleButton.current.clientWidth || 360),
    });
  }, [scriptReady]);

  useEffect(() => {
    renderGoogleButton();
    return () => window.google?.accounts.id.cancel();
  }, [credential, renderGoogleButton]);

  async function deleteAccount() {
    if (!credential) return;
    const token = credential;
    setCredential(null);
    setEmail("");
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/account/deletion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: token }),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          error?: { message?: string };
        } | null;
        throw new Error(
          body?.error?.message ||
            "Deletion could not be completed. Please try again.",
        );
      }
      setComplete(true);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Deletion could not be completed.",
      );
      setScriptReady((ready) => !ready);
      queueMicrotask(() => setScriptReady(true));
    } finally {
      setBusy(false);
    }
  }

  if (complete) {
    return (
      <section className="completion" role="status">
        <span>✓</span>
        <h2>Your Goodgrocer account was deleted.</h2>
        <p>
          Your Google account was not affected. A future sign-in creates a new
          Goodgrocer account.
        </p>
        <a className="button secondary" href="/">
          Return home
        </a>
      </section>
    );
  }

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={() => setScriptReady(true)}
      />
      <section className="deletion-card">
        <h2>What deletion means</h2>
        <ul>
          <li>
            Your Goodgrocer identity, sessions, saved addresses and favourites
            are deleted.
          </li>
          <li>
            Active orders continue, but you lose account access and order
            tracking.
          </li>
          <li>
            Active delivery details are erased at completion or within 30 days.
          </li>
          <li>
            Signing in later creates a new account without restoring history.
          </li>
          <li>
            This website cannot erase a basket stored only on another device;
            clear the app&apos;s storage or uninstall it to remove that local
            data.
          </li>
        </ul>
        {!credential ? (
          <div className="auth-step">
            <h3>1. Verify your Google account</h3>
            <p>Choose the same Google account used with Goodgrocer.</p>
            {clientId ? (
              <div className="google-button" ref={googleButton} />
            ) : (
              <p className="notice">
                Google authentication is not configured for this website yet.
              </p>
            )}
          </div>
        ) : (
          <div className="confirm-step">
            <p className="eyebrow">SELECTED GOOGLE ACCOUNT</p>
            <strong>{email}</strong>
            <h3>2. Permanently delete this Goodgrocer account?</h3>
            <p>
              This action cannot be undone and does not cancel active orders.
            </p>
            <button
              className="button danger"
              onClick={deleteAccount}
              disabled={busy}
            >
              {busy ? "Deleting…" : "Delete Goodgrocer account"}
            </button>
            <button
              className="button-link"
              onClick={() => {
                setCredential(null);
                setEmail("");
                renderGoogleButton();
              }}
            >
              Choose a different account
            </button>
          </div>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <p className="help">
          Need help? Email{" "}
          <a href="mailto:somnathprasad559@gmail.com">
            somnathprasad559@gmail.com
          </a>
          .
        </p>
      </section>
    </>
  );
}
