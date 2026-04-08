import { ArrowRight, Boxes, Network, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import Dashboard from "./Dashboard";
import { getSandboxEmailFromLocation } from "../sandbox/isSandboxAppUrl";
import { getAccessUserEmail, startCheckout } from "../services/api";
import { getStripePaymentLink } from "../services/stripeLinks";

type SandboxFeature = {
  title: string;
  description: string;
  icon: typeof Network;
  emphasized?: boolean;
};

const SANDBOX_FEATURES: SandboxFeature[] = [
  {
    title: "System Breakdown",
    description: "Automatically extract tags, control loops, IO, and logic from your documents.",
    icon: Network,
  },
  {
    title: "Engineering Workspace",
    description: "View, edit, simulate, and explore your full system in a structured, interactive workspace.",
    icon: Boxes,
  },
  {
    title: "Plant Genie (AI)",
    description: "Ask questions about your system or live plant data and get instant, actionable answers.",
    icon: Sparkles,
    emphasized: true,
  },
];

const SANDBOX_STEPS = [
  {
    title: "Upload your documents",
    description: "Upload your P&ID and control narrative.",
  },
  {
    title: "Review generated outputs",
    description: "View your automatically generated control logic and IO mapping.",
  },
  {
    title: "Query with Plant Genie",
    description: "Ask Plant Genie about your system or live data to uncover insights instantly.",
  },
] as const;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Sandbox() {
  const sandboxEmail = useMemo(() => getSandboxEmailFromLocation(), []);
  const dismissedKey = useMemo(() => `industrypath:sandbox:onboarding:dismissed:${sandboxEmail}`, [sandboxEmail]);
  const resolvedCheckoutEmail = useMemo(() => {
    const fromUrl = sandboxEmail.trim().toLowerCase();
    if (EMAIL_RE.test(fromUrl)) {
      return fromUrl;
    }
    const fromSession = getAccessUserEmail().trim().toLowerCase();
    return EMAIL_RE.test(fromSession) ? fromSession : "";
  }, [sandboxEmail]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [checkoutMessage, setCheckoutMessage] = useState("");
  const [startingCheckout, setStartingCheckout] = useState<"solo" | "team" | "">("");
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("yearly");
  const [checkoutEmail, setCheckoutEmail] = useState(resolvedCheckoutEmail);
  const [open, setOpen] = useState(() => {
    if (typeof window === "undefined") {
      return true;
    }
    return window.localStorage.getItem(dismissedKey) !== "1";
  });

  const closeModal = (): void => {
    setOpen(false);
    try {
      window.localStorage.setItem(dismissedKey, "1");
    } catch {
      // Ignore storage failures and still close the modal.
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("modal")?.toLowerCase() === "pricing-access" && params.get("from")?.toLowerCase() === "sandbox") {
      setShowUpgradeModal(true);
    }
  }, []);

  useEffect(() => {
    if (resolvedCheckoutEmail) {
      setCheckoutEmail(resolvedCheckoutEmail);
    }
  }, [resolvedCheckoutEmail]);

  const startPaidCheckout = async (plan: "solo" | "team", cycle: "monthly" | "yearly"): Promise<void> => {
    const normalized = checkoutEmail.trim().toLowerCase();
    if (!EMAIL_RE.test(normalized)) {
      setCheckoutMessage("Enter a valid email to continue to checkout.");
      return;
    }
    setCheckoutMessage("");
    setStartingCheckout(plan);
    try {
      const frontendStripe = getStripePaymentLink(plan, cycle === "monthly", normalized);
      if (frontendStripe) {
        if (frontendStripe.startsWith("price:")) {
          const returnUrl = new URL(window.location.origin + "/");
          returnUrl.searchParams.set("checkout", "success");
          returnUrl.searchParams.set("checkout_plan", plan);
          returnUrl.searchParams.set("checkout_email", normalized);
          returnUrl.searchParams.set("maintenance", "0");

          const cancelUrl = new URL(window.location.href);
          cancelUrl.searchParams.delete("modal");
          cancelUrl.searchParams.delete("from");

          const session = await startCheckout({
            email: normalized,
            plan,
            maintenance: false,
            billing_cycle: cycle,
            success_url: returnUrl.toString(),
            cancel_url: cancelUrl.toString(),
          });
          if (!session.url) {
            setCheckoutMessage("Could not start checkout.");
            return;
          }
          window.location.assign(session.url);
          return;
        }
        window.location.assign(frontendStripe);
        return;
      }
      // Frontend link not provided: fallback to backend checkout session (price-id flow).
      const returnUrl = new URL(window.location.origin + "/");
      returnUrl.searchParams.set("checkout", "success");
      returnUrl.searchParams.set("checkout_plan", plan);
      returnUrl.searchParams.set("checkout_email", normalized);
      returnUrl.searchParams.set("maintenance", "0");

      const cancelUrl = new URL(window.location.href);
      cancelUrl.searchParams.delete("modal");
      cancelUrl.searchParams.delete("from");

      const session = await startCheckout({
        email: normalized,
        plan,
        maintenance: false,
        billing_cycle: cycle,
        success_url: returnUrl.toString(),
        cancel_url: cancelUrl.toString(),
      });
      if (!session.url) {
        setCheckoutMessage("Could not start checkout.");
        return;
      }
      window.location.assign(session.url);
      return;
    } catch (error) {
      setCheckoutMessage(error instanceof Error ? error.message : "Could not start checkout.");
    } finally {
      setStartingCheckout("");
    }
  };

  return (
    <>
      {open ? (
        <div
          className="modal-backdrop"
          onClick={closeModal}
          role="dialog"
          aria-modal="true"
          aria-label="Sandbox onboarding"
          style={{ zIndex: 60 }}
        >
          <div
            className="modal-card sandbox-onboarding-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="sandbox-onboarding-section sandbox-onboarding-hero">
              <div className="sandbox-onboarding-hero-copy">
                <div className="sandbox-onboarding-eyebrow">IndustryPath Sandbox</div>
                <h1>Turn your system into a live, queryable model in seconds.</h1>
                <p>
                  Upload your P&amp;ID and control narrative, generate control logic, simulate your plant data, &amp; interact
                  with your system using AI.
                </p>
              </div>
              <button
                type="button"
                onClick={closeModal}
                className="command-btn"
              >
                Close
              </button>
            </div>

            <div className="sandbox-onboarding-section sandbox-onboarding-features">
              <div className="sandbox-onboarding-card-grid">
                {SANDBOX_FEATURES.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <article
                      key={feature.title}
                      className={`sandbox-onboarding-card ${feature.emphasized ? "is-emphasized" : ""}`}
                    >
                      <div className="sandbox-onboarding-card-icon" aria-hidden="true">
                        <Icon size={18} />
                      </div>
                      <h2>{feature.title}</h2>
                      <p>{feature.description}</p>
                    </article>
                  );
                })}
              </div>
            </div>

            <div className="sandbox-onboarding-section sandbox-onboarding-actions">
              <div className="sandbox-onboarding-actions-copy">
                <h2>Getting Started</h2>
                <ol className="sandbox-onboarding-steps">
                  {SANDBOX_STEPS.map((step) => (
                    <li key={step.title}>
                      <span className="sandbox-onboarding-step-number" aria-hidden="true" />
                      <div className="sandbox-onboarding-step-copy">
                        <strong>{step.title}</strong>
                        <span>{step.description}</span>
                      </div>
                    </li>
                  ))}
                </ol>
                <p className="sandbox-onboarding-note">Sandbox includes full access. Limited to 3 exports.</p>
              </div>
              <button type="button" className="command-btn primary sandbox-onboarding-cta" onClick={closeModal}>
                <span>Start Building Your System</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showUpgradeModal ? (
        <div className="modal-backdrop" onClick={() => setShowUpgradeModal(false)} role="dialog" aria-modal="true" aria-label="Upgrade options">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} style={{ maxWidth: 700, width: "min(94vw, 700px)", borderRadius: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <h3 style={{ margin: 0, fontSize: 28, letterSpacing: "-0.02em" }}>Choose your paid plan</h3>
              <button type="button" className="command-btn" onClick={() => setShowUpgradeModal(false)}>
                Close
              </button>
            </div>
            <p style={{ marginTop: 0, color: "#64748b", marginBottom: 14, fontSize: 17 }}>
              Select Solo or Teams to continue to Stripe checkout.
            </p>
            <div style={{ display: "inline-flex", border: "1px solid #cbd5e1", borderRadius: 10, padding: 4, marginBottom: 14 }}>
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
            <label style={{ display: "block", marginBottom: 8, fontWeight: 700, color: "#1e293b" }}>Billing email</label>
            <input
              type="email"
              value={checkoutEmail}
              onChange={(event) => setCheckoutEmail(event.target.value)}
              placeholder="you@company.com"
              style={{
                width: "100%",
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "11px 12px",
                fontSize: 16,
                marginBottom: 14,
              }}
            />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <button
                type="button"
                className="command-btn"
                disabled={Boolean(startingCheckout)}
                onClick={() => void startPaidCheckout("solo", billingCycle)}
                style={{ borderRadius: 12, padding: "14px 12px", border: "1px solid #cbd5e1", background: "#f8fafc" }}
              >
                <span style={{ display: "block", fontWeight: 800, fontSize: 20, marginBottom: 4 }}>Solo</span>
                <span style={{ color: "#64748b", fontSize: 13 }}>
                  {startingCheckout === "solo"
                    ? "Starting..."
                    : billingCycle === "monthly"
                      ? "$97/month"
                      : "$997/year · 2 months free"}
                </span>
              </button>
              <button
                type="button"
                className="command-btn primary"
                disabled={Boolean(startingCheckout)}
                onClick={() => void startPaidCheckout("team", billingCycle)}
                style={{
                  borderRadius: 12,
                  padding: "14px 12px",
                  border: "1px solid #b91c1c",
                  background: "linear-gradient(180deg, #ef4444 0%, #dc2626 100%)",
                }}
              >
                <span style={{ display: "block", fontWeight: 800, fontSize: 20, marginBottom: 4 }}>Teams</span>
                <span style={{ color: "rgba(255,255,255,0.92)", fontSize: 13 }}>
                  {startingCheckout === "team"
                    ? "Starting..."
                    : billingCycle === "monthly"
                      ? "$297/month"
                      : "$2,997/year · 2 months free"}
                </span>
              </button>
            </div>
            {checkoutMessage ? <p style={{ marginTop: 12, color: "#b91c1c", fontWeight: 600 }}>{checkoutMessage}</p> : null}
          </div>
        </div>
      ) : null}

      <Dashboard mode="sandbox" sandboxEmail={sandboxEmail} onSandboxUpgradeNow={() => setShowUpgradeModal(true)} />
    </>
  );
}
