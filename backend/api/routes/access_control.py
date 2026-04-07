from __future__ import annotations

import os
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from services.access_control_service import access_control_service

router = APIRouter(prefix="/access", tags=["access"])
logger = logging.getLogger(__name__)
DEFAULT_PRICE_LOOKUPS = {
    "solo_license": "pandaura_solo_license_usd_onetime",
    "team_license": "pandaura_team_license_usd_onetime",
    "solo_maintenance": "pandaura_solo_maintenance_usd_monthly",
    "team_maintenance": "pandaura_team_maintenance_usd_monthly",
}


def _email(value: str | None) -> str:
    return (value or "").strip().lower()


def _resolve_email(payload_email: Any, header_email: str | None) -> str:
    resolved = _email(str(payload_email or "")) or _email(header_email)
    if not resolved:
        raise HTTPException(status_code=400, detail="email is required")
    return resolved


@router.post("/identify")
def identify(payload: dict[str, Any]) -> dict[str, Any]:
    return access_control_service.identify(str(payload.get("email") or ""))


@router.post("/register")
def register(payload: dict[str, Any]) -> dict[str, Any]:
    user = access_control_service.ensure_user(
        str(payload.get("email") or ""),
        account_type=str(payload.get("account_type") or "sandbox"),
        paid_plan=str(payload.get("paid_plan")) if payload.get("paid_plan") else None,
    )
    return {"user": user}


@router.post("/login")
def login(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return access_control_service.login(str(payload.get("email") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/session")
def session(token: str) -> dict[str, Any]:
    user = access_control_service.session(token)
    if not user:
        raise HTTPException(status_code=404, detail="session not found")
    return {"user": user}


@router.post("/logout")
def logout(payload: dict[str, Any]) -> dict[str, Any]:
    access_control_service.logout(str(payload.get("token") or ""))
    return {"success": True}


@router.get("/sandbox/status")
def sandbox_status(email: str) -> dict[str, Any]:
    return access_control_service.sandbox_status(email)


@router.post("/sandbox/export/increment")
def sandbox_increment(payload: dict[str, Any]) -> dict[str, Any]:
    email = str(payload.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    return access_control_service.increment_sandbox_export(email)


@router.post("/checkout/start")
def checkout_start(payload: dict[str, Any]) -> dict[str, Any]:
    email = _email(str(payload.get("email") or ""))
    plan = str(payload.get("plan") or "").lower()
    maintenance = bool(payload.get("maintenance"))
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    if plan not in {"solo", "team"}:
        raise HTTPException(status_code=400, detail="plan must be solo or team")
    # Capture checkout email as source-of-truth identity even before completion.
    access_control_service.ensure_user(email, account_type="sandbox")

    fallback = f"/checkout/mock?plan={plan}&email={email}&maintenance={int(maintenance)}"
    secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not secret:
        return {"url": fallback}

    try:
        import stripe  # type: ignore

        stripe.api_key = secret
        success_url = str(payload.get("success_url") or "http://localhost:5173/?checkout=success")
        cancel_url = str(payload.get("cancel_url") or "http://localhost:5173/?checkout=canceled")
        license_env_key = "STRIPE_PRICE_TEAM_LICENSE" if plan == "team" else "STRIPE_PRICE_SOLO_LICENSE"
        maintenance_env_key = "STRIPE_PRICE_TEAM_MAINTENANCE" if plan == "team" else "STRIPE_PRICE_SOLO_MAINTENANCE"
        lookup_license_env_key = (
            "STRIPE_LOOKUP_KEY_TEAM_LICENSE" if plan == "team" else "STRIPE_LOOKUP_KEY_SOLO_LICENSE"
        )
        lookup_maintenance_env_key = (
            "STRIPE_LOOKUP_KEY_TEAM_MAINTENANCE" if plan == "team" else "STRIPE_LOOKUP_KEY_SOLO_MAINTENANCE"
        )
        license_lookup_default = DEFAULT_PRICE_LOOKUPS["team_license" if plan == "team" else "solo_license"]
        maintenance_lookup_default = DEFAULT_PRICE_LOOKUPS["team_maintenance" if plan == "team" else "solo_maintenance"]

        def _matches_mode(price_obj: Any, *, expect_recurring: bool | None) -> bool:
            if expect_recurring is None:
                return True
            recurring = getattr(price_obj, "recurring", None)
            is_recurring = recurring is not None
            return is_recurring if expect_recurring else not is_recurring

        def resolve_active_price(
            explicit_price_id: str, *, lookup_key: str, expect_recurring: bool | None, keyword_hint: str
        ) -> str:
            candidate = (explicit_price_id or "").strip()
            if candidate:
                try:
                    retrieved = stripe.Price.retrieve(candidate)
                    if bool(getattr(retrieved, "active", False)) and _matches_mode(
                        retrieved, expect_recurring=expect_recurring
                    ):
                        return candidate
                    logger.warning("stripe price id is inactive: %s", candidate)
                except Exception:
                    logger.exception("stripe price retrieve failed for id=%s", candidate)
            lookup = (lookup_key or "").strip()
            if not lookup:
                return ""
            listed = stripe.Price.list(lookup_keys=[lookup], active=True, limit=10)
            for item in listed.data:
                if _matches_mode(item, expect_recurring=expect_recurring):
                    return str(item.id)
            # Fallback: discover likely active prices by product/price metadata.
            # This keeps checkout working if lookup keys drift between repos.
            try:
                catalog = stripe.Price.list(active=True, limit=100, expand=["data.product"])
                hint = keyword_hint.strip().lower()
                for item in catalog.data:
                    if not _matches_mode(item, expect_recurring=expect_recurring):
                        continue
                    parts = [str(getattr(item, "lookup_key", "") or ""), str(getattr(item, "nickname", "") or "")]
                    product = getattr(item, "product", None)
                    if hasattr(product, "get"):
                        parts.append(str(product.get("name", "") or ""))
                        metadata = product.get("metadata", {}) or {}
                        parts.append(" ".join(f"{k}:{v}" for k, v in metadata.items()))
                    haystack = " ".join(parts).lower()
                    if hint and hint in haystack:
                        return str(item.id)
            except Exception:
                logger.exception("stripe catalog fallback lookup failed")
            return ""

        license_price_id = resolve_active_price(
            os.getenv(license_env_key, ""),
            lookup_key=os.getenv(lookup_license_env_key, "").strip() or license_lookup_default,
            expect_recurring=None,
            keyword_hint="team license" if plan == "team" else "solo license",
        )
        maintenance_price_id = resolve_active_price(
            os.getenv(maintenance_env_key, ""),
            lookup_key=os.getenv(lookup_maintenance_env_key, "").strip() or maintenance_lookup_default,
            expect_recurring=True,
            keyword_hint="team maintenance" if plan == "team" else "solo maintenance",
        )

        if not license_price_id:
            return {"url": fallback}

        line_items = [{"price": license_price_id, "quantity": 1}]
        mode = "payment"
        try:
            license_price = stripe.Price.retrieve(license_price_id)
            if getattr(license_price, "recurring", None) is not None:
                mode = "subscription"
        except Exception:
            logger.exception("stripe license price retrieve failed for id=%s", license_price_id)
        if maintenance:
            if not maintenance_price_id:
                return {"url": fallback}
            line_items.append({"price": maintenance_price_id, "quantity": 1})
            mode = "subscription"

        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=line_items,
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"plan": plan, "maintenance": "1" if maintenance else "0", "email": email},
        )
        checkout_url = getattr(session, "url", None)
        if not checkout_url and isinstance(session, dict):
            checkout_url = session.get("url")
        return {"url": str(checkout_url or fallback)}
    except Exception as exc:
        logger.exception("stripe checkout start failed for plan=%s email=%s: %s", plan, email, exc)
        return {"url": fallback}


@router.post("/checkout/complete")
def checkout_complete(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        user = access_control_service.complete_checkout(
            email=str(payload.get("email") or ""),
            plan=str(payload.get("plan") or ""),
            maintenance=bool(payload.get("maintenance")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user": user}


@router.get("/billing")
def billing(email: str | None = None, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    return access_control_service.billing(_resolve_email(email, x_user_email))


@router.post("/billing/maintenance/cancel")
def cancel_maintenance(payload: dict[str, Any], x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    user = access_control_service.cancel_maintenance(_resolve_email(payload.get("email"), x_user_email))
    return {"user": user}


@router.post("/teams/invite")
def invite(payload: dict[str, Any], x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    admin_email = _resolve_email(payload.get("admin_email"), x_user_email)
    emails = payload.get("emails") or []
    if not isinstance(emails, list):
        raise HTTPException(status_code=400, detail="emails must be list")
    try:
        return access_control_service.invite_team_members(admin_email, [str(item) for item in emails])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/teams/members")
def remove_team_member(member_email: str, admin_email: str | None = None, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    resolved_admin = _resolve_email(admin_email, x_user_email)
    try:
        return access_control_service.remove_team_member(resolved_admin, member_email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/teams/setup/acknowledge")
def acknowledge_team_setup(payload: dict[str, Any], x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    resolved = _resolve_email(payload.get("email"), x_user_email)
    return {"user": access_control_service.acknowledge_team_setup_prompt(resolved)}


@router.get("/rbac")
def rbac(email: str | None = None, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    resolved = _resolve_email(email, x_user_email)
    return {"roles": access_control_service.team_roles(resolved), "permissions": access_control_service.permissions_for_email(resolved)}


@router.post("/rbac/set-role")
def set_role(payload: dict[str, Any], x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, Any]:
    admin = _resolve_email(payload.get("admin_email"), x_user_email)
    try:
        roles = access_control_service.set_role(admin, str(payload.get("member_email") or ""), str(payload.get("role") or ""))
        return {"roles": roles}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
