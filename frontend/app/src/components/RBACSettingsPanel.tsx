import { useEffect, useMemo, useState } from "react";
import { getRbacState, setTeamMemberRole } from "../services/api";

const ROLES = ["admin", "member"] as const;
type Role = (typeof ROLES)[number];

export default function RBACSettingsPanel() {
  const [members, setMembers] = useState<Record<string, string>>({});
  const [permissions, setPermissions] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");

  const refresh = async (): Promise<void> => {
    try {
      const data = await getRbacState();
      setMembers(data.roles.members ?? {});
      setPermissions(data.permissions ?? {});
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load RBAC state.");
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const memberRows = useMemo(() => Object.entries(members), [members]);

  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view">
        <div className="billing-settings-card">
          <h2 className="panel-title">RBAC</h2>
          <p className="billing-settings-lead">Manage team roles and backend-enforced permissions.</p>
          <div style={{ marginBottom: 10 }}>
            <strong>Effective permissions:</strong>{" "}
            {Object.entries(permissions)
              .filter(([, allowed]) => allowed)
              .map(([name]) => name)
              .join(", ") || "none"}
          </div>
          {memberRows.length === 0 ? (
            <p className="billing-settings-sub">No team members found.</p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {memberRows.map(([email, role]) => (
                <div key={email} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                  <span className="value-mono">{email}</span>
                  <select
                    value={role}
                    onChange={(event) => {
                      void setTeamMemberRole(email, event.target.value as Role).then(() => refresh());
                    }}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}
          {error ? <p style={{ marginTop: 10, color: "#a11" }}>{error}</p> : null}
        </div>
      </div>
    </section>
  );
}
