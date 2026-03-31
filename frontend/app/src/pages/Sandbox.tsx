import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import Dashboard from "./Dashboard";
import { getSandboxEmailFromLocation } from "../sandbox/isSandboxAppUrl";

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

  const Column = ({ title, children }: { title: string; children: ReactNode }) => (
    <div
      style={{
        border: "1px solid var(--stroke)",
        background: "var(--panel)",
        borderRadius: 14,
        padding: "14px 14px",
        minHeight: 118,
      }}
    >
      <div style={{ fontWeight: 800, color: "var(--text)", marginBottom: 8 }}>{title}</div>
      <div style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.35 }}>{children}</div>
    </div>
  );

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
            className="modal-card"
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "min(980px, calc(100vw - 2rem))",
              padding: 0,
              borderRadius: 10,
              background: "var(--panel-strong)",
              color: "var(--text)",
            }}
          >
            <div
              style={{
                padding: "18px 18px 10px",
                borderBottom: "1px solid var(--stroke)",
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: 14,
              }}
            >
              <div>
                <div style={{ fontSize: 26, fontWeight: 900, lineHeight: 1.1, marginBottom: 6 }}>Welcome to IndustryPath</div>
                <div style={{ color: "var(--muted)", fontSize: 13 }}>Understand your system instantly. No setup required.</div>
              </div>
              <button
                type="button"
                onClick={closeModal}
                className="command-btn"
              >
                Close
              </button>
            </div>

            <div style={{ padding: "14px 18px 12px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                <Column title="Left panel">
                  Access the engineering table, control loops, IO mapping, generated control logic, and Plant Genie.
                </Column>
                <Column title="Center">
                  The main workspace where selected tabs render and users interact with the system.
                </Column>
                <Column title="Plant Genie">
                  Query live plant data and get clear, actionable answers instantly.
                </Column>
              </div>

              <div style={{ marginTop: 12, color: "var(--muted)", fontSize: 12, lineHeight: 1.35 }}>
                Tip: Use the modules from the left to explore the system. Exports are limited to 3 in sandbox.
              </div>
              <div style={{ marginTop: 8, color: "var(--text)", fontSize: 12.5, lineHeight: 1.4, fontWeight: 600 }}>
                To get started, create a new project and upload your P&amp;ID and Control Narrative.
              </div>
            </div>

            <div
              style={{
                padding: "12px 18px 18px",
                borderTop: "1px solid var(--stroke)",
                display: "flex",
                justifyContent: "flex-end",
              }}
            >
              <button type="button" className="command-btn primary" onClick={closeModal}>
                Start Exploring
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <Dashboard mode="sandbox" sandboxEmail={sandboxEmail} />
    </>
  );
}
