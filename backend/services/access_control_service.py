from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TEAM_MEMBER_LIMIT = 10


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future_iso(*, days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat()


class AccessControlService:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2] / "storage"
        root.mkdir(parents=True, exist_ok=True)
        self._path = root / "access_control.json"
        self._state = self._load()

    def _default_state(self) -> dict[str, Any]:
        return {"users": {}, "sessions": {}, "sandbox_exports": {}, "teams": {}}

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return self._default_state()
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                state = self._default_state()
                state.update(payload)
                return state
        except Exception:
            pass
        return self._default_state()

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    @staticmethod
    def _email(email: str) -> str:
        return (email or "").strip().lower()

    @staticmethod
    def _workspace_key(value: str, *, prefix: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
        slug = slug or secrets.token_hex(4)
        return f"{prefix}-{slug}"[:120]

    def _default_user(self, email: str, *, account_type: str = "sandbox", paid_plan: str | None = None) -> dict[str, Any]:
        return {
            "email": email,
            "account_type": account_type,
            "paid_plan": paid_plan,
            "maintenance_active": False,
            "maintenance_cancel_at_period_end": False,
            "team_id": None,
            "workspace_id": None,
            "role": "viewer",
            "permissions": {},
            "next_payment_date_iso": None,
            "team_setup_prompt_pending": False,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

    def _normalize_team_members(self, team: dict[str, Any]) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        raw_members = team.get("members") or {}
        if isinstance(raw_members, dict):
            for email, value in raw_members.items():
                key = self._email(str(email or ""))
                if not key:
                    continue
                if isinstance(value, dict):
                    normalized[key] = {
                        "role": str(value.get("role") or "member").strip().lower() or "member",
                        "added_at": str(value.get("added_at") or team.get("created_at") or _now_iso()),
                    }
                else:
                    normalized[key] = {
                        "role": str(value or "member").strip().lower() or "member",
                        "added_at": str(team.get("created_at") or _now_iso()),
                    }
        team["members"] = normalized
        team["member_limit"] = int(team.get("member_limit") or TEAM_MEMBER_LIMIT)
        team["workspace_id"] = str(team.get("workspace_id") or team.get("id") or self._workspace_key(str(team.get("owner_email") or "team"), prefix="workspace"))
        return normalized

    def _normalize_user(self, user: dict[str, Any]) -> dict[str, Any]:
        normalized = self._default_user(self._email(str(user.get("email") or "")))
        normalized.update(user)
        normalized["email"] = self._email(str(normalized.get("email") or ""))
        normalized["role"] = str(normalized.get("role") or "viewer").strip().lower() or "viewer"
        normalized["workspace_id"] = normalized.get("workspace_id") or None
        normalized["team_id"] = normalized.get("team_id") or None
        normalized["team_setup_prompt_pending"] = bool(normalized.get("team_setup_prompt_pending"))
        normalized["permissions"] = dict(normalized.get("permissions") or {})
        normalized["next_payment_date_iso"] = normalized.get("next_payment_date_iso") or None
        return normalized

    def _get_team(self, team_id: str | None) -> dict[str, Any] | None:
        key = str(team_id or "").strip()
        if not key:
            return None
        team = self._state["teams"].get(key)
        if not isinstance(team, dict):
            return None
        self._normalize_team_members(team)
        return team

    def _public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_user(user)
        team = self._get_team(normalized.get("team_id"))
        team_members = []
        if team is not None:
            team_members = sorted(team["members"].keys())
        return {
            "email": normalized["email"],
            "account_type": normalized.get("account_type", "sandbox"),
            "paid_plan": normalized.get("paid_plan"),
            "maintenance_active": bool(normalized.get("maintenance_active")),
            "maintenance_cancel_at_period_end": bool(normalized.get("maintenance_cancel_at_period_end")),
            "team_id": normalized.get("team_id"),
            "workspace_id": normalized.get("workspace_id"),
            "role": normalized.get("role") or "viewer",
            "next_payment_date_iso": normalized.get("next_payment_date_iso"),
            "team_setup_prompt_pending": bool(normalized.get("team_setup_prompt_pending")),
            "team_members": team_members,
            "member_limit": int(team.get("member_limit") or TEAM_MEMBER_LIMIT) if team else TEAM_MEMBER_LIMIT,
        }

    def workspace_id_for_email(self, email: str) -> str:
        user = self.ensure_user(email)
        workspace_id = str(user.get("workspace_id") or "").strip()
        if workspace_id:
            return workspace_id
        if user.get("paid_plan") == "team" and user.get("team_id"):
            return str(user.get("team_id"))
        return self._workspace_key(user["email"], prefix="workspace")

    def _team_member_count(self, team: dict[str, Any]) -> int:
        members = self._normalize_team_members(team)
        owner = self._email(str(team.get("owner_email") or ""))
        return sum(1 for email in members if email and email != owner)

    def ensure_user(self, email: str, *, account_type: str = "sandbox", paid_plan: str | None = None) -> dict[str, Any]:
        key = self._email(email)
        if not key:
            raise ValueError("email is required")
        user = self._state["users"].get(key)
        if user is None:
            user = self._default_user(key, account_type=account_type, paid_plan=paid_plan)
            self._state["users"][key] = user
            self._save()
        else:
            user = self._normalize_user(user)
            if paid_plan and not user.get("paid_plan"):
                user["paid_plan"] = paid_plan
            if account_type and user.get("account_type") == "sandbox" and account_type != "sandbox":
                user["account_type"] = account_type
            self._state["users"][key] = user
        return user

    def identify(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        user = self._state["users"].get(key)
        return {"exists": user is not None, "user": self._public_user(user) if user else None}

    def login(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        user = self._state["users"].get(key)
        if user is None:
            raise ValueError("Unknown user")
        token = secrets.token_urlsafe(24)
        self._state["sessions"][token] = {"email": key, "created_at": _now_iso()}
        self._save()
        return {"token": token, "user": self._public_user(user)}

    def logout(self, token: str) -> None:
        normalized = (token or "").strip()
        if not normalized:
            return
        self._state["sessions"].pop(normalized, None)
        self._save()

    def session(self, token: str) -> dict[str, Any] | None:
        item = self._state["sessions"].get((token or "").strip())
        if not item:
            return None
        user = self._state["users"].get(item["email"])
        return self._public_user(user) if user else None

    def sandbox_status(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        user = self._state["users"].get(key)
        used = int(self._state["sandbox_exports"].get(key, 0))
        return {
            "email": key,
            "known_user": user is not None,
            "account_type": (user or {}).get("account_type", "unknown"),
            "paid_plan": (user or {}).get("paid_plan"),
            "exports_used": used,
            "export_limit": 3,
            "read_only": used >= 3,
        }

    def increment_sandbox_export(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        self._state["sandbox_exports"][key] = int(self._state["sandbox_exports"].get(key, 0)) + 1
        self._save()
        return self.sandbox_status(key)

    def complete_checkout(self, email: str, plan: str, maintenance: bool) -> dict[str, Any]:
        if plan not in {"solo", "team"}:
            raise ValueError("plan must be solo or team")
        user = self.ensure_user(email, account_type="paid", paid_plan=plan)
        user["account_type"] = "paid"
        user["paid_plan"] = plan
        user["maintenance_active"] = bool(maintenance)
        user["maintenance_cancel_at_period_end"] = False
        user["next_payment_date_iso"] = user.get("next_payment_date_iso") or _future_iso(days=30)
        user["updated_at"] = _now_iso()
        if plan == "team":
            team_id = user.get("team_id") or f"team-{secrets.token_hex(4)}"
            user["team_id"] = team_id
            user["workspace_id"] = team_id
            user["role"] = "admin"
            user["team_setup_prompt_pending"] = True
            team = self._get_team(team_id)
            if team is None:
                self._state["teams"][team_id] = {
                    "id": team_id,
                    "owner_email": user["email"],
                    "workspace_id": team_id,
                    "member_limit": TEAM_MEMBER_LIMIT,
                    "members": {user["email"]: {"role": "admin", "added_at": _now_iso()}},
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }
            else:
                members = self._normalize_team_members(team)
                members[user["email"]] = {"role": "admin", "added_at": members.get(user["email"], {}).get("added_at", _now_iso())}
                team["owner_email"] = user["email"]
                team["workspace_id"] = team_id
                team["updated_at"] = _now_iso()
        else:
            user["team_id"] = None
            user["workspace_id"] = user.get("workspace_id") or self._workspace_key(user["email"], prefix="workspace")
            user["role"] = "admin"
            user["team_setup_prompt_pending"] = False
        self._save()
        return self._public_user(user)

    def cancel_maintenance(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        user["maintenance_cancel_at_period_end"] = True
        user["updated_at"] = _now_iso()
        self._save()
        return self._public_user(user)

    def invite_team_members(self, admin_email: str, emails: list[str]) -> dict[str, Any]:
        admin = self.ensure_user(admin_email)
        team_id = admin.get("team_id")
        team = self._get_team(team_id)
        if not team_id or team is None:
            raise ValueError("Team not found")
        if admin.get("role") != "admin":
            raise ValueError("Only team admin can invite")
        members = self._normalize_team_members(team)
        normalized_emails = []
        duplicates = []
        for raw in emails:
            key = self._email(raw)
            if not key:
                continue
            if key in normalized_emails or key in members:
                duplicates.append(key)
            else:
                normalized_emails.append(key)
        if duplicates:
            raise ValueError(f"Duplicate team member email: {sorted(set(duplicates))[0]}")
        if self._team_member_count(team) + len(normalized_emails) > int(team.get("member_limit") or TEAM_MEMBER_LIMIT):
            raise ValueError(f"You can add up to {int(team.get('member_limit') or TEAM_MEMBER_LIMIT)} team members.")
        added: list[str] = []
        for key in normalized_emails:
            member = self.ensure_user(key)
            member["account_type"] = "paid"
            member["paid_plan"] = "team"
            member["team_id"] = team_id
            member["workspace_id"] = str(team.get("workspace_id") or team_id)
            member["role"] = "member"
            member["team_setup_prompt_pending"] = False
            member["updated_at"] = _now_iso()
            members[key] = {"role": "member", "added_at": _now_iso()}
            added.append(key)
        team["updated_at"] = _now_iso()
        self._save()
        return {"team_id": team_id, "added": sorted(set(added)), "members": self.team_roles(admin_email)["members"]}

    def remove_team_member(self, admin_email: str, member_email: str) -> dict[str, Any]:
        admin = self.ensure_user(admin_email)
        if admin.get("role") != "admin":
            raise ValueError("Only team admin can remove members")
        team = self._get_team(admin.get("team_id"))
        if team is None:
            raise ValueError("Team not found")
        key = self._email(member_email)
        owner_email = self._email(str(team.get("owner_email") or ""))
        if key == owner_email:
            raise ValueError("Team admin cannot remove themselves")
        members = self._normalize_team_members(team)
        if key not in members:
            raise ValueError("member not in team")
        members.pop(key, None)
        member = self.ensure_user(key)
        member["team_id"] = None
        member["workspace_id"] = None
        member["paid_plan"] = None
        member["account_type"] = "sandbox"
        member["role"] = "viewer"
        member["team_setup_prompt_pending"] = False
        member["updated_at"] = _now_iso()
        team["updated_at"] = _now_iso()
        self._save()
        return {"team_id": team["id"], "members": self.team_roles(admin_email)["members"]}

    def acknowledge_team_setup_prompt(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        user["team_setup_prompt_pending"] = False
        user["updated_at"] = _now_iso()
        self._save()
        return self._public_user(user)

    def billing(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        tier = "Team" if user.get("paid_plan") == "team" else "Solo" if user.get("paid_plan") == "solo" else "Sandbox"
        team = self._get_team(user.get("team_id"))
        members = []
        if team is not None:
            for member_email, record in sorted(self._normalize_team_members(team).items()):
                members.append(
                    {
                        "email": member_email,
                        "role": str(record.get("role") or "member"),
                        "is_admin": member_email == self._email(str(team.get("owner_email") or "")),
                        "added_at": record.get("added_at"),
                    }
                )
        return {
            "email": user["email"],
            "license_tier": tier,
            "product_name": "Industry Path Pro",
            "maintenance_active": bool(user.get("maintenance_active")),
            "maintenance_cancel_at_period_end": bool(user.get("maintenance_cancel_at_period_end")),
            "maintenance_note": "Included with your current subscription term." if user.get("maintenance_active") else None,
            "paid_plan": user.get("paid_plan"),
            "team_id": user.get("team_id"),
            "workspace_id": user.get("workspace_id"),
            "role": user.get("role") or "viewer",
            "next_payment_date_iso": user.get("next_payment_date_iso"),
            "can_manage_team": user.get("role") == "admin",
            "team_setup_prompt_pending": bool(user.get("team_setup_prompt_pending")),
            "member_limit": int(team.get("member_limit") or TEAM_MEMBER_LIMIT) if team else TEAM_MEMBER_LIMIT,
            "team_members": members,
        }

    def team_roles(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        team = self._get_team(user.get("team_id"))
        if team is None:
            return {"team_id": None, "members": {}}
        members = self._normalize_team_members(team)
        return {
            "team_id": team["id"],
            "owner": team.get("owner_email"),
            "members": {member_email: str(record.get("role") or "member") for member_email, record in sorted(members.items())},
        }

    def set_role(self, admin_email: str, member_email: str, role: str) -> dict[str, Any]:
        if role not in {"admin", "member"}:
            raise ValueError("role must be admin/member")
        admin = self.ensure_user(admin_email)
        if admin.get("role") != "admin":
            raise ValueError("Only admin can assign roles")
        team_id = admin.get("team_id")
        team = self._get_team(team_id)
        if not team_id or team is None:
            raise ValueError("Team not found")
        key = self._email(member_email)
        members = self._normalize_team_members(team)
        if key not in members:
            raise ValueError("member not in team")
        members[key]["role"] = role
        member = self.ensure_user(key)
        member["role"] = role
        member["updated_at"] = _now_iso()
        self._save()
        return {"team_id": team_id, "members": team["members"]}

    def permissions_for_email(self, email: str) -> dict[str, bool]:
        user = self.ensure_user(email)
        role = (user.get("role") or "viewer").lower()
        base = {
            "create_edit_logic": role in {"admin", "member"},
            "run_simulation": role in {"admin", "member"},
            "export": role in {"admin", "member"},
            "manage_members": role == "admin",
            "billing": role == "admin",
        }
        overrides = user.get("permissions") or {}
        for key, value in overrides.items():
            base[str(key)] = bool(value)
        return base

    def authorize(self, email: str | None, action: str) -> tuple[bool, str]:
        key = self._email(email or "")
        if not key:
            return False, "X-User-Email header is required"
        user = self.ensure_user(key)
        if user.get("account_type") == "sandbox":
            status = self.sandbox_status(key)
            if status["read_only"] and action in {"create_edit_logic", "run_simulation", "export"}:
                return False, "Sandbox export limit reached. Upgrade required."
        perms = self.permissions_for_email(key)
        if not perms.get(action, False):
            return False, "Your role does not allow this action"
        return True, ""


access_control_service = AccessControlService()
