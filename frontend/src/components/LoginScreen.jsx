// Full-screen login/landing gate shown when the app is in live mode but not yet
// connected to Google Health. Login itself happens on Google's site (OAuth 2.0):
// this button just starts that redirect flow at the backend's /auth/login.
export default function LoginScreen({ error }) {
  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-logo">🧬</div>
        <h1 className="brand">Jarvis<span>Health</span></h1>
        <p className="login-sub">
          Melde dich mit deinem Google-Konto an, um deine Fitbit-/Google-Health-Daten
          zu synchronisieren.
        </p>

        <a className="btn primary login-btn" href="/api/auth/login">
          <span className="g-icon">G</span> Mit Google anmelden
        </a>

        <p className="login-note">
          Die Anmeldung erfolgt sicher auf der offiziellen Google-Seite. Dein
          Passwort wird dieser App nie übermittelt – Google gibt lediglich einen
          Zugriffstoken zurück, den du jederzeit widerrufen kannst.
        </p>

        {error && <div className="login-error">{error}</div>}

        <details className="login-help">
          <summary>Voraussetzung: Google-OAuth-Client einrichten</summary>
          <p>
            Damit die Anmeldung funktioniert, muss einmalig ein OAuth-Client in der
            Google Cloud Console angelegt und in <code>backend/.env</code> hinterlegt
            werden (Client-ID/Secret, Redirect-URI
            <code> http://localhost:8000/auth/callback</code>). Details stehen in der
            <code> README.md</code>. Zum Ausprobieren ohne Konto:
            <code> USE_MOCK_PROVIDER=true</code>.
          </p>
        </details>
      </div>
    </div>
  );
}
