import type { ChatMessage, LlmConfig, SessionSummary, SkillSummary, ToolCall } from "./types";

const API_BASE = "";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + url, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  const data = (await res.json().catch(() => ({}))) as T & { detail?: string };
  if (!res.ok) {
    const msg = (data as any).detail || res.statusText || "请求失败";
    throw new Error(msg);
  }
  return data;
}

export async function fetchSessions(userId: string): Promise<SessionSummary[]> {
  const uid = (userId || "").trim() || "default";
  const data = await fetchJson<{ sessions: SessionSummary[] }>(
    `/api/sessions?user_id=${encodeURIComponent(uid)}`,
  );
  return data.sessions || [];
}

export async function fetchHistory(sessionId: string): Promise<ChatMessage[]> {
  const data = await fetchJson<{ messages: { role: "user" | "assistant"; content: string }[] }>(
    `/api/history?session_id=${encodeURIComponent(sessionId)}`,
  );
  return (data.messages || []) as ChatMessage[];
}

export async function deleteSessionApi(sessionId: string, userId: string): Promise<void> {
  const uid = (userId || "").trim() || "default";
  await fetchJson(
    `/api/sessions/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(uid)}`,
    { method: "DELETE" },
  );
}

export async function sendChat(
  params: { sessionId?: string; userId?: string; message: string },
): Promise<{ session_id: string; reply: string; tool_calls?: ToolCall[] }> {
  const body = {
    session_id: params.sessionId || undefined,
    user_id: params.userId || undefined,
    message: params.message,
  };
  return fetchJson("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchConfig(): Promise<LlmConfig> {
  return fetchJson<LlmConfig>("/api/config");
}

export async function updateConfig(body: {
  model: string;
  base_url: string;
  api_key?: string;
}): Promise<LlmConfig & { api_key_set: boolean }> {
  return fetchJson("/api/config", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function fetchModels(params?: {
  base_url?: string;
  api_key?: string;
}): Promise<string[]> {
  const hasOverride = !!(params?.base_url || params?.api_key);
  const data = await fetchJson<{ models: string[] }>(
    "/api/config/models",
    hasOverride
      ? { method: "POST", body: JSON.stringify(params) }
      : { method: "GET" },
  );
  return data.models || [];
}

export async function fetchSkills(): Promise<SkillSummary[]> {
  const data = await fetchJson<SkillSummary[]>("/api/skills");
  return data;
}

