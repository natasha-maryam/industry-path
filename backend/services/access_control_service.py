from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    def ensure_user(self, email: str, *, account_type: str = "sandbox", paid_plan: str | None = None) -> dict[str, Any]:
        key = self._email(email)
        if not key:
            raise ValueError("email is required")
        user = self._state["users"].get(key)
        if user is None:
            user = {
                "email": key,
                "account_type": account_type,
                "paid_plan": paid_plan,
                "maintenance_active": False,
                "maintenance_cancel_at_period_end": False,
                "team_id": None,
                "role": "viewer",
                "permissions": {},
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            self._state["users"][key] = user
            self._save()
        return user

    def identify(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        user = self._state["users"].get(key)
        return {"exists": user is not None, "user": user}

    def login(self, email: str) -> dict[str, Any]:
        key = self._email(email)
        user = self._state["users"].get(key)
        if user is None:
            raise ValueError("Unknown user")
        token = secrets.token_urlsafe(24)
        self._state["sessions"][token] = {"email": key, "created_at": _now_iso()}
        self._save()
        return {"token": token, "user": user}

    def session(self, token: str) -> dict[str, Any] | None:
        item = self._state["sessions"].get((token or "").strip())
        if not item:
            return None
        return self._state["users"].get(item["email"])

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
        user["updated_at"] = _now_iso()
        if plan == "team":
            team_id = user.get("team_id") or f"team-{secrets.token_hex(4)}"
            user["team_id"] = team_id
            user["role"] = "admin"
            if team_id not in self._state["teams"]:
                self._state["teams"][team_id] = {
                    "id": team_id,
                    "owner_email": user["email"],
                    "members": {user["email"]: "admin"},
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }
        self._save()
        return user

    def cancel_maintenance(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        user["maintenance_cancel_at_period_end"] = True
        user["updated_at"] = _now_iso()
        self._save()
        return user

    def invite_team_members(self, admin_email: str, emails: list[str]) -> dict[str, Any]:
        admin = self.ensure_user(admin_email)
        team_id = admin.get("team_id")
        if not team_id or team_id not in self._state["teams"]:
            raise ValueError("Team not found")
        if admin.get("role") != "admin":
            raise ValueError("Only team admin can invite")
        team = self._state["teams"][team_id]
        added: list[str] = []
        for raw in emails:
            key = self._email(raw)
            if not key:
                continue
            member = self.ensure_user(key)
            member["account_type"] = "paid"
            member["paid_plan"] = "team"
            member["team_id"] = team_id
            member["role"] = team["members"].get(key, "editor")
            member["updated_at"] = _now_iso()
            team["members"][key] = member["role"]
            added.append(key)
        team["updated_at"] = _now_iso()
        self._save()
        return {"team_id": team_id, "added": sorted(set(added)), "members": team["members"]}

    def billing(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        tier = "Team" if user.get("paid_plan") == "team" else "Solo" if user.get("paid_plan") == "solo" else "Sandbox"
        return {
            "email": user["email"],
            "license_tier": tier,
            "maintenance_active": bool(user.get("maintenance_active")),
            "maintenance_cancel_at_period_end": bool(user.get("maintenance_cancel_at_period_end")),
            "paid_plan": user.get("paid_plan"),
            "team_id": user.get("team_id"),
            "role": user.get("role") or "viewer",
        }

    def team_roles(self, email: str) -> dict[str, Any]:
        user = self.ensure_user(email)
        team_id = user.get("team_id")
        if not team_id or team_id not in self._state["teams"]:
            return {"team_id": None, "members": {}}
        return {"team_id": team_id, "members": self._state["teams"][team_id]["members"]}

    def set_role(self, admin_email: str, member_email: str, role: str) -> dict[str, Any]:
        if role not in {"admin", "editor", "viewer"}:
            raise ValueError("role must be admin/editor/viewer")
        admin = self.ensure_user(admin_email)
        if admin.get("role") != "admin":
            raise ValueError("Only admin can assign roles")
        team_id = admin.get("team_id")
        if not team_id or team_id not in self._state["teams"]:
            raise ValueError("Team not found")
        team = self._state["teams"][team_id]
        key = self._email(member_email)
        if key not in team["members"]:
            raise ValueError("member not in team")
        team["members"][key] = role
        member = self.ensure_user(key)
        member["role"] = role
        member["updated_at"] = _now_iso()
        self._save()
        return {"team_id": team_id, "members": team["members"]}

    def permissions_for_email(self, email: str) -> dict[str, bool]:
        user = self.ensure_user(email)
        role = (user.get("role") or "viewer").lower()
        base = {
            "create_edit_logic": role in {"admin", "editor"},
            "run_simulation": role in {"admin", "editor"},
            "export": role in {"admin", "editor"},
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
