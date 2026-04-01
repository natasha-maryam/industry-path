import { useEffect, useMemo, useState } from "react";
import Sandbox from "./Sandbox";
import {
  completeCheckout,
  getAccessSession,
  getSandboxStatus,
  identifyAccessUser,
  loginAccessUser,
  registerAccessUser,
  startCheckout,
  setAccessUserEmail,
} from "../services/api";
import { getSandboxEmailFromLocation } from "../sandbox/isSandboxAppUrl";
import { getStripePaymentLink } from "../services/stripeLinks";

const TOKEN_KEY = "industrypath:access:token";
const LANDING_URL = "https://industrypath.tech";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function SandboxAccessGate() {
  const hintedEmail = useMemo(() => getSandboxEmailFromLocation(""), []);
  const [email, setEmail] = useState(hintedEmail);
  const [phase, setPhase] = useState<"loading" | "blocked" | "login" | "sandbox">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const run = async (): Promise<void> => {
      const params = new URLSearchParams(window.location.search);
      const checkoutPlan = params.get("checkout_plan");
      const checkoutEmail = params.get("checkout_email");
      if (checkoutPlan && checkoutEmail && (checkoutPlan === "solo" || checkoutPlan === "team")) {
        await completeCheckout({ email: checkoutEmail, plan: checkoutPlan, maintenance: params.get("maintenance") === "1" });
      }

      const token = window.localStorage.getItem(TOKEN_KEY) || "";
      if (token) {
        try {
          const user = await getAccessSession(token);
          const normalized = user.email;
          await identifyAccessUser(normalized);
          setAccessUserEmail(normalized);
          if (user.account_type === "paid") {
            window.location.href = "/";
            return;
          }
          setEmail(normalized);
          setPhase("sandbox");
          return;
        } catch {
          window.localStorage.removeItem(TOKEN_KEY);
        }
      }

      if (!hintedEmail) {
        setPhase("login");
        return;
      }

      // If URL carries a valid email, persist it once for access tracking.
      if (EMAIL_RE.test(hintedEmail)) {
        const identified = await identifyAccessUser(hintedEmail);
        if (!identified.exists) {
          await registerAccessUser({ email: hintedEmail, account_type: "sandbox" });
        }
        setPhase("login");
        return;
      }
      setPhase("blocked");
    };
    void run().catch(() => {
      setMessage("Could not verify access. Please try again.");
      setPhase("blocked");
    });
  }, [hintedEmail]);

  const handleLogin = async (): Promise<void> => {
    setMessage("");
    const normalized = email.trim().toLowerCase();
    if (!normalized) {
      setMessage("Enter your email.");
      return;
    }
    try {
      const { exists } = await identifyAccessUser(normalized);
      if (!exists) {
        setMessage("Unknown account. Please use the landing page first.");
        setPhase("blocked");
        return;
      }
      const session = await loginAccessUser(normalized);
      window.localStorage.setItem(TOKEN_KEY, session.token);
      setAccessUserEmail(normalized);
      const status = await getSandboxStatus(normalized);
      if (status.account_type === "paid") {
        window.location.href = "/";
        return;
      }
      setPhase("sandbox");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    }
  };

  const startPaidCheckout = async (plan: "solo" | "team"): Promise<void> => {
    const normalized = email.trim().toLowerCase();
    if (!normalized) {
      setMessage("Enter your email first.");
      return;
    }
    const frontendStripe = getStripePaymentLink(plan, true, normalized);
    if (frontendStripe) {
      window.location.href = frontendStripe;
      return;
    }
    const returnUrl = new URL(window.location.origin + "/");
    returnUrl.searchParams.set("checkout", "success");
    returnUrl.searchParams.set("checkout_plan", plan);
    returnUrl.searchParams.set("checkout_email", normalized);
    returnUrl.searchParams.set("maintenance", "1");

    const cancelUrl = new URL(window.location.origin + "/");
    cancelUrl.searchParams.set("checkout", "canceled");

    const session = await startCheckout({
      email: normalized,
      plan,
      maintenance: true,
      success_url: returnUrl.toString(),
      cancel_url: cancelUrl.toString(),
    });
    if (!session.url) {
      setMessage("Could not start checkout.");
      return;
    }
    window.location.href = session.url;
  };

  if (phase === "sandbox") {
    return <Sandbox />;
  }

  if (phase === "blocked") {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#6f1d1d", color: "white", padding: 24 }}>
        <div style={{ textAlign: "center", maxWidth: 560 }}>
          <h1 style={{ fontSize: 34, marginBottom: 8 }}>Access blocked</h1>
          <p style={{ fontSize: 18, marginBottom: 8 }}>Please go to the landing page for access to IndustryPath.</p>
          <a href={LANDING_URL} style={{ color: "#ffd7d7", textDecoration: "underline", fontWeight: 700 }}>
            {LANDING_URL}
          </a>
          {message ? <p style={{ marginTop: 14 }}>{message}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background:
          "radial-gradient(circle at top, rgba(220, 38, 38, 0.06), transparent 45%), linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 560,
          border: "1px solid #e2e8f0",
          borderRadius: 18,
          padding: 24,
          background: "#ffffff",
          boxShadow: "0 22px 45px rgba(15, 23, 42, 0.08)",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 6, fontSize: 34, letterSpacing: "-0.02em", color: "#0f172a" }}>IndustryPath Login</h2>
        <p style={{ marginTop: 0, marginBottom: 14, color: "#64748b", fontSize: 16 }}>Sign in to continue to sandbox.</p>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@company.com"
          style={{
            width: "100%",
            padding: "12px 14px",
            border: "1px solid #cbd5e1",
            borderRadius: 12,
            fontSize: 17,
            outline: "none",
          }}
        />
        <button
          type="button"
          className="command-btn primary"
          style={{
            marginTop: 12,
            minWidth: 112,
            borderRadius: 10,
            padding: "10px 16px",
            fontWeight: 700,
            background: "linear-gradient(180deg, #ef4444 0%, #dc2626 100%)",
            border: "1px solid #b91c1c",
          }}
          onClick={() => void handleLogin()}
        >
          Login
        </button>
        <div style={{ marginTop: 22, borderTop: "1px solid #e2e8f0", paddingTop: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 10, fontSize: 29, letterSpacing: "-0.02em", color: "#0f172a" }}>Upgrade from sandbox</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <button
              type="button"
              className="command-btn"
              style={{
                borderRadius: 12,
                border: "1px solid #cbd5e1",
                background: "#f8fafc",
                padding: "11px 12px",
                fontWeight: 700,
              }}
              onClick={() => void startPaidCheckout("solo")}
            >
              Buy Solo
            </button>
            <button
              type="button"
              className="command-btn"
              style={{
                borderRadius: 12,
                border: "1px solid #b91c1c",
                background: "linear-gradient(180deg, #ef4444 0%, #dc2626 100%)",
                color: "#fff",
                padding: "11px 12px",
                fontWeight: 700,
              }}
              onClick={() => void startPaidCheckout("team")}
            >
              Buy Teams
            </button>
          </div>
          <p style={{ fontSize: 13, color: "#64748b", marginTop: 10 }}>Maintenance is included yearly by default.</p>
        </div>
        {message ? <p style={{ marginTop: 12, color: "#b91c1c", fontWeight: 600 }}>{message}</p> : null}
      </div>
    </div>
  );
}
