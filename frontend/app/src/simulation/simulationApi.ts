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

export async function testConnector(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/simulation/connectors/test`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function activateConnector(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/simulation/connectors/activate`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

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

export async function registerAI(payload: { id: string; endpoint: string; apiKey?: string }): Promise<void> {
  const response = await fetch(`${API_BASE}/simulation/ai/register`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function queryAI(payload: { prompt: string; connectorId: string }): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/simulation/ai/query`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function applyAIAction(payload: { id: string; value: unknown }): Promise<void> {
  const response = await fetch(`${API_BASE}/simulation/ai/apply-action`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export function createSimulationEventSource(): EventSource {
  return new EventSource(`${API_BASE}/simulation/stream`);
}

export async function getSimulationState(): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/simulation/state`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getSimulationHealth(): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/simulation/health`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getSimulationChangelog(): Promise<Array<Record<string, unknown>>> {
  const response = await fetch(`${API_BASE}/simulation/changelog`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getSimulationEventsReplay(): Promise<Array<Record<string, unknown>>> {
  const response = await fetch(`${API_BASE}/simulation/events/replay`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
