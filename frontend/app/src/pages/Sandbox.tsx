import { ArrowRight, Boxes, Network, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import Dashboard from "./Dashboard";
import { getSandboxEmailFromLocation } from "../sandbox/isSandboxAppUrl";

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

export default function Sandbox() {
  const sandboxEmail = useMemo(() => getSandboxEmailFromLocation(), []);
  const dismissedKey = useMemo(() => `industrypath:sandbox:onboarding:dismissed:${sandboxEmail}`, [sandboxEmail]);
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

      <Dashboard mode="sandbox" sandboxEmail={sandboxEmail} />
    </>
  );
}
