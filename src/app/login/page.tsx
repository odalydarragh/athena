import { loginAction } from "./actions";

export default function LoginPage() {
  return (
    <main className="wrap">
      <h1>Sign in (demo)</h1>
      <p className="lede">
        Demo mode uses example.com accounts only. No passwords are stored. Cookie{" "}
        <code>documdr_session</code> is HttpOnly and strictly necessary.
      </p>
      <form action={loginAction}>
        <label htmlFor="email">Work email</label>
        <input id="email" name="email" type="email" defaultValue="qa@example.com" required />
        <p>
          <button type="submit">Continue</button>
        </p>
      </form>
      <p className="mono">eng@example.com (engineer) · qa@example.com (quality)</p>
    </main>
  );
}
