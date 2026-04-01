const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const DEFAULT_API_BASE_URL = "https://industry-path-production.up.railway.app/";

const normalizedApiOrigin = (API_BASE_URL || DEFAULT_API_BASE_URL).trim().replace(/\/$/, "");

export { API_BASE_URL };

export const API_BASE = `${normalizedApiOrigin}/api`;

export const WS_BASE_URL = normalizedApiOrigin
  .replace(/^http:\/\//i, "ws://")
  .replace(/^https:\/\//i, "wss://");