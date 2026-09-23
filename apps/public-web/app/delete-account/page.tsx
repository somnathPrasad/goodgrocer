import DeleteAccountFlow from "./DeleteAccountFlow";

export const metadata = { title: "Delete account · Goodgrocer" };

export default function DeleteAccountPage() {
  return (
    <main className="delete-page">
      <div className="delete-intro">
        <p className="eyebrow">ACCOUNT CONTROL</p>
        <h1>Delete your Goodgrocer account.</h1>
        <p>
          This page works independently of the Android app. Verify the Google
          account you used with Goodgrocer, review the consequences, and confirm
          deletion.
        </p>
      </div>
      <DeleteAccountFlow />
    </main>
  );
}
