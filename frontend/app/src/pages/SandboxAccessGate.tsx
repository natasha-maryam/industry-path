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
const ACCOUNT_TYPE_KEY = "industrypath:access:account_type";
const LANDING_URL = "https://industrypath.tech";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function SandboxAccessGate() {
  const hintedEmail = useMemo(() => getSandboxEmailFromLocation(""), []);
  const [email, setEmail] = useState(hintedEmail);
  const [phase, setPhase] = useState<"loading" | "blocked" | "login" | "sandbox">("loading");
  const [message, setMessage] = useState("");
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("yearly");

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
          window.localStorage.setItem(ACCOUNT_TYPE_KEY, user.account_type);
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

      // If URL carries a valid email, auto-register/login and continue straight into sandbox.
      if (EMAIL_RE.test(hintedEmail)) {
        try {
          // Idempotent on backend: existing users are reused, new users are created.
          await registerAccessUser({ email: hintedEmail, account_type: "sandbox" });
          const session = await loginAccessUser(hintedEmail);
          window.localStorage.setItem(TOKEN_KEY, session.token);
          setAccessUserEmail(hintedEmail);
          window.localStorage.setItem(ACCOUNT_TYPE_KEY, session.user.account_type);
          setPhase("sandbox");
          return;
        } catch {
          // If bootstrap calls fail, keep the user in login flow instead of blocking access.
          setEmail(hintedEmail);
          setMessage("Could not auto-sign in. Please tap Login to continue.");
          setPhase("login");
          return;
        }
      }
      setPhase("blocked");
    };
    void run().catch(() => {
      // Network/startup hiccups should not hard-block users from the sandbox path.
      if (EMAIL_RE.test(hintedEmail)) {
        setEmail(hintedEmail);
        setMessage("Could not verify access right now. Please tap Login to continue.");
        setPhase("login");
        return;
      }
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
      window.localStorage.setItem(ACCOUNT_TYPE_KEY, session.user.account_type);
      const status = await getSandboxStatus(normalized);
      if (status.account_type === "paid") {
        window.localStorage.setItem(ACCOUNT_TYPE_KEY, "paid");
        window.location.href = "/";
        return;
      }
      window.localStorage.setItem(ACCOUNT_TYPE_KEY, "sandbox");
      setPhase("sandbox");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    }
  };

  const startPaidCheckout = async (plan: "solo" | "team", cycle: "monthly" | "yearly"): Promise<void> => {
    const normalized = email.trim().toLowerCase();
    if (!normalized) {
      setMessage("Enter your email first.");
      return;
    }
    const frontendStripe = getStripePaymentLink(plan, cycle === "monthly", normalized);
    if (frontendStripe) {
      if (frontendStripe.startsWith("price:")) {
        const returnUrl = new URL(window.location.origin + "/");
        returnUrl.searchParams.set("checkout", "success");
        returnUrl.searchParams.set("checkout_plan", plan);
        returnUrl.searchParams.set("checkout_email", normalized);
        returnUrl.searchParams.set("maintenance", "0");

        const cancelUrl = new URL(window.location.origin + "/");
        cancelUrl.searchParams.set("checkout", "canceled");

        const session = await startCheckout({
          email: normalized,
          plan,
          maintenance: false,
          billing_cycle: cycle,
          success_url: returnUrl.toString(),
          cancel_url: cancelUrl.toString(),
        });
        if (!session.url) {
          setMessage("Could not start checkout.");
          return;
        }
        window.location.href = session.url;
        return;
      }
      window.location.href = frontendStripe;
      return;
    }
    // Frontend link missing: fallback to backend checkout session (price-id flow).
    const returnUrl = new URL(window.location.origin + "/");
    returnUrl.searchParams.set("checkout", "success");
    returnUrl.searchParams.set("checkout_plan", plan);
    returnUrl.searchParams.set("checkout_email", normalized);
    returnUrl.searchParams.set("maintenance", "0");

    const cancelUrl = new URL(window.location.origin + "/");
    cancelUrl.searchParams.set("checkout", "canceled");

    const session = await startCheckout({
      email: normalized,
      plan,
      maintenance: false,
      billing_cycle: cycle,
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
          <div style={{ display: "inline-flex", border: "1px solid #cbd5e1", borderRadius: 10, padding: 4, marginBottom: 10 }}>
            <button
              type="button"
              className="command-btn"
              onClick={() => setBillingCycle("monthly")}
              style={{ borderRadius: 8, padding: "8px 12px", background: billingCycle === "monthly" ? "#fff" : "transparent" }}
            >
              Monthly
            </button>
            <button
              type="button"
              className="command-btn"
              onClick={() => setBillingCycle("yearly")}
              style={{ borderRadius: 8, padding: "8px 12px", background: billingCycle === "yearly" ? "#fff" : "transparent" }}
            >
              Yearly
            </button>
          </div>
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
              onClick={() => void startPaidCheckout("solo", billingCycle)}
            >
              {billingCycle === "monthly" ? "Buy Solo · $97/mo" : "Buy Solo · $997/yr"}
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
              onClick={() => void startPaidCheckout("team", billingCycle)}
            >
              {billingCycle === "monthly" ? "Buy Teams · $297/mo" : "Buy Teams · $2,997/yr"}
            </button>
          </div>
          {billingCycle === "yearly" ? (
            <p style={{ fontSize: 13, color: "#047857", marginTop: 10, fontWeight: 600 }}>2 months free</p>
          ) : null}
        </div>
        {message ? <p style={{ marginTop: 12, color: "#b91c1c", fontWeight: 600 }}>{message}</p> : null}
      </div>
    </div>
  );
}
