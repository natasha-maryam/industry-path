const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const DEFAULT_API_BASE_URL = "https://industry-path-production.up.railway.app/";

const isLocalFrontend =
  typeof window !== "undefined" &&
  ["localhost", "127.0.0.1"].includes(window.location.hostname) &&
  window.location.port === "5173";

const normalizedApiOrigin = (API_BASE_URL || (isLocalFrontend ? window.location.origin : DEFAULT_API_BASE_URL))
  .trim()
  .replace(/\/$/, "");

export { API_BASE_URL };

export const API_BASE = `${normalizedApiOrigin}/api`;

export const WS_BASE_URL = normalizedApiOrigin
  .replace(/^http:\/\//i, "ws://")
  .replace(/^https:\/\//i, "wss://");