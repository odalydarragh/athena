import { requireUser } from "../../../lib/session";
import { eraseSelfAction } from "../export/actions";

export default async function PrivacyAccountPage() {
  await requireUser();
  return (
    <main className="wrap">
      <h1>Your data</h1>
      <p>
        Access and erasure for your account (GDPR Arts. 15 and 17). Git author handles are
        minimised on erase. See the <a href="/privacy">privacy notice</a>.
      </p>
      <p>
        <a className="btn" href="/app/privacy/export">
          Download my data (JSON)
        </a>
      </p>
      <form action={eraseSelfAction}>
        <p>
          <button type="submit" className="secondary">
            Erase my user record
          </button>
        </p>
      </form>
    </main>
  );
}
