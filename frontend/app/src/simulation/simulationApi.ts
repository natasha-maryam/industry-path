import { API_BASE } from "../config/api";

const jsonHeaders = { "Content-Type": "application/json" };

const parseError = async (response: Response): Promise<string> => {
  const text = await response.text();
  try {
    const parsed = JSON.parse(text) as { detail?: string };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail;
    }
  } catch {
    // Ignore parse failures and return raw text.
  }
  return text || `Request failed (${response.status})`;
};

export async function applyOverride(payload: { id: string; value: unknown }): Promise<void> {
  const response = await fetch(`${API_BASE}/simulation/override`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function removeOverride(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/simulation/override/remove`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ id }),
  });
  if (!response.ok) throw new Error(await parseError(response));
}
