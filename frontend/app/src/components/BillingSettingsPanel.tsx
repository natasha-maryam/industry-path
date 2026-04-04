import { LoaderCircle, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { addTeamMembers, getBillingState, removeTeamMember, type BillingState } from "../services/api";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const DEMO_TEAM_EMAILS = [
  "controls.lead@demo-industrypath.com",
  "operations.manager@demo-industrypath.com",
  "maintenance.supervisor@demo-industrypath.com",
];
const DEMO_NEXT_PAYMENT_DATE = "2026-05-04";

type DemoTeamMember = BillingState["team_members"][number];

const INITIAL_DEMO_TEAM_MEMBERS: DemoTeamMember[] = DEMO_TEAM_EMAILS.map((email) => ({
  email,
  role: "member",
  is_admin: false,
  added_at: null,
}));

function formatDate(isoDate?: string | null): string {
  if (!isoDate) {
    return "Not scheduled";
  }
  const d = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(d.getTime())) {
    return isoDate;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "long",
  }).format(d);
}

export default function BillingSettingsPanel() {
  const { user } = useAuth();
  const [billing, setBilling] = useState<BillingState | null>(null);
  const [demoTeamMembers, setDemoTeamMembers] = useState<DemoTeamMember[]>(INITIAL_DEMO_TEAM_MEMBERS);
  const [inviteEmail, setInviteEmail] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [removingEmail, setRemovingEmail] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");

  const refresh = async (): Promise<void> => {
    if (!user?.email) {
      setBilling(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const nextBilling = await getBillingState(user.email);
      setBilling(nextBilling);
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Could not load billing state.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, [user?.email]);

  const isDemoPreview = !billing || billing.paid_plan !== "team";

  const effectiveBilling = useMemo<BillingState | null>(() => {
    if (billing && billing.paid_plan === "team") {
      return billing;
    }
    return {
      email: user?.email || "demo-admin@industrypath.com",
      license_tier: "Team",
      product_name: "Industry Path Pro",
      maintenance_active: true,
      maintenance_cancel_at_period_end: false,
      maintenance_note: "Demo workspace for client walkthrough.",
      paid_plan: "team",
      team_id: "team-demo-preview",
      workspace_id: "team-demo-preview",
      role: "admin",
      next_payment_date_iso: DEMO_NEXT_PAYMENT_DATE,
      can_manage_team: true,
      team_setup_prompt_pending: false,
      member_limit: 10,
      team_members: demoTeamMembers,
    };
  }, [billing, demoTeamMembers, user?.email]);

  const teamMemberCount = useMemo(() => {
    if (!effectiveBilling) {
      return 0;
    }
    return effectiveBilling.team_members.filter((member) => !member.is_admin).length;
  }, [effectiveBilling]);

  const remainingSeats = useMemo(() => {
    if (!effectiveBilling) {
      return 0;
    }
    return Math.max(0, effectiveBilling.member_limit - teamMemberCount);
  }, [effectiveBilling, teamMemberCount]);

  const handleAddMember = async (): Promise<void> => {
    const normalized = inviteEmail.trim().toLowerCase();
    if (!EMAIL_RE.test(normalized)) {
      setError("Enter a valid team member email.");
      return;
    }
    if (effectiveBilling?.team_members.some((member) => member.email.toLowerCase() === normalized)) {
      setError("That team member already exists.");
      return;
    }
    if (remainingSeats <= 0) {
      setError("No seats left for additional team members.");
      return;
    }

    if (isDemoPreview) {
      setDemoTeamMembers((current) => [...current, { email: normalized, role: "member", is_admin: false, added_at: null }]);
      setInviteEmail("");
      setError("");
      setSuccessMessage(`${normalized} added to the demo Teams workspace.`);
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccessMessage("");
    try {
      await addTeamMembers([normalized], user?.email);
      setInviteEmail("");
      setSuccessMessage(`${normalized} added to your Teams workspace.`);
      await refresh();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Could not add team member.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveMember = async (memberEmail: string): Promise<void> => {
    if (isDemoPreview) {
      setDemoTeamMembers((current) => current.filter((member) => member.email !== memberEmail));
      setError("");
      setSuccessMessage(`${memberEmail} removed from the demo workspace.`);
      return;
    }

    setRemovingEmail(memberEmail);
    setError("");
    setSuccessMessage("");
    try {
      await removeTeamMember(memberEmail, user?.email);
      setSuccessMessage(`${memberEmail} removed from the workspace.`);
      await refresh();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Could not remove team member.");
    } finally {
      setRemovingEmail("");
    }
  };


  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view">
        <div className="billing-settings-stack">
          <div className="billing-settings-card">
            <h2 className="panel-title">Billing</h2>
            <p className="billing-settings-lead">Subscription and license details for your organization.</p>

            {isLoading ? (
              <div className="billing-settings-inline-state">
                <LoaderCircle size={14} className="animate-spin" /> Loading subscription details...
              </div>
            ) : effectiveBilling ? (
              <>
                <dl className="kv billing-settings-kv">
                  <dt>Current license</dt>
                  <dd>
                    {effectiveBilling.license_tier} — {effectiveBilling.product_name}
                  </dd>

                  <dt>Maintenance</dt>
                  <dd>
                    {effectiveBilling.maintenance_active ? (
                      <>
                        <span className="billing-status billing-status-active">Active</span>
                        {effectiveBilling.maintenance_note ? <span className="billing-settings-sub">{effectiveBilling.maintenance_note}</span> : null}
                      </>
                    ) : (
                      <span className="billing-status billing-status-inactive">Not active</span>
                    )}
                  </dd>

                  <dt>Next payment</dt>
                  <dd className="value-mono">{formatDate(effectiveBilling.next_payment_date_iso)}</dd>

                  <dt>Workspace role</dt>
                  <dd>{effectiveBilling.role === "admin" ? "Admin" : "Team Member"}</dd>
                </dl>

                {effectiveBilling.paid_plan === "team" ? (
                  <div className="billing-team-summary">
                    <div className="billing-team-chip">
                      <Users size={13} />
                      <span>
                        {teamMemberCount}/{effectiveBilling.member_limit} team members added
                      </span>
                    </div>
                    <div className="billing-team-chip">
                      <span>{remainingSeats} seats remaining</span>
                    </div>
                    {isDemoPreview ? (
                      <div className="billing-team-chip">
                        <span>Demo preview</span>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </>
            ) : null}
          </div>

          <div className="billing-settings-card">
            <h3 className="panel-subtitle">Team Access</h3>
            <p className="billing-settings-lead">
              {effectiveBilling?.paid_plan === "team"
                ? "Admins can add and remove up to 10 team members by email. All team users share the same workspace and project space."
                : "Upgrade to Teams to manage shared workspace membership from Billing."}
            </p>
            {isDemoPreview ? <p className="billing-settings-sub">Showing a built-in Teams demo workspace so you can present the member-management flow.</p> : null}

            {error ? <div className="billing-settings-alert is-error">{error}</div> : null}
            {successMessage ? <div className="billing-settings-alert is-success">{successMessage}</div> : null}

            {effectiveBilling?.paid_plan === "team" ? (
              <>
                {effectiveBilling.can_manage_team ? (
                  <>
                    <div className="billing-team-add-row">
                      <input
                        className="modal-input"
                        type="email"
                        value={inviteEmail}
                        onChange={(event) => setInviteEmail(event.target.value)}
                        placeholder="team.member@company.com"
                      />
                      <button className="command-btn primary" type="button" onClick={() => void handleAddMember()} disabled={isSaving || remainingSeats <= 0}>
                        {isSaving ? "Adding..." : "Add Member"}
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="billing-settings-sub">Only the team admin can manage members from Billing.</p>
                )}

                <div className="billing-team-list">
                  {effectiveBilling.team_members.length === 0 ? (
                    <p className="billing-settings-sub">No team members have been added yet.</p>
                  ) : (
                    effectiveBilling.team_members.map((member) => (
                      <div key={member.email} className="billing-team-member-row">
                        <div className="billing-team-member-copy">
                          <strong>{member.email}</strong>
                          <span>{member.is_admin ? "Admin" : "Team Member"}</span>
                        </div>
                        {effectiveBilling.can_manage_team && !member.is_admin ? (
                          <button
                            className="command-btn"
                            type="button"
                            onClick={() => void handleRemoveMember(member.email)}
                            disabled={removingEmail === member.email}
                          >
                            <Trash2 size={12} />
                            <span>{removingEmail === member.email ? "Removing..." : "Remove"}</span>
                          </button>
                        ) : null}
                      </div>
                    ))
                  )}
                </div>
              </>
            ) : (
              <p className="billing-settings-sub">Teams billing unlocks shared workspace access, admin member management, and up to 10 teammate seats.</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}