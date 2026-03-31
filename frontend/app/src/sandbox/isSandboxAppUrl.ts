/**
 * True when the current URL should load sandbox mode (demo, no DB-backed project list).
 * Supports:
 * - Path: /sandbox
 * - Query: ?plan=sandbox (landing / pricing funnel)
 * - Hash query: #?plan=sandbox or #/path?plan=sandbox (some hosts put params after #)
 */
export function isSandboxAppUrl(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const path = (window.location.pathname || "/").replace(/\/+$/, "") || "/";
  if (path === "/sandbox" || path.endsWith("/sandbox")) {
    return true;
  }

  const searchParams = new URLSearchParams(window.location.search ?? "");
  if (searchParams.get("plan")?.toLowerCase() === "sandbox") {
    return true;
  }

  const hash = window.location.hash ?? "";
  if (!hash || hash.length <= 1) {
    return false;
  }

  const hashQuery =
    hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : hash.startsWith("#") ? hash.slice(1) : hash;
  const hashParams = new URLSearchParams(hashQuery);
  return hashParams.get("plan")?.toLowerCase() === "sandbox";
}

/** Email from ?email= or hash query (pricing funnel). */
export function getSandboxEmailFromLocation(fallback = "free-user"): string {
  if (typeof window === "undefined") {
    return fallback;
  }
  const fromSearch = new URLSearchParams(window.location.search ?? "");
  let email = fromSearch.get("email") || "";
  if (!email && window.location.hash) {
    const hash = window.location.hash;
    const hashQuery = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : hash.startsWith("#") ? hash.slice(1) : hash;
    email = new URLSearchParams(hashQuery).get("email") || "";
  }
  const trimmed = (email || "").trim().toLowerCase();
  return trimmed || fallback;
}
