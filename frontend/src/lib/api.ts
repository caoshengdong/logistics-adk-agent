import { getToken, removeToken } from "./auth";
import type { ChatSession, ChatMessage, SSEEvent, TokenResponse, User } from "@/types";

/**
 * API base URL:
 * - Production: set NEXT_PUBLIC_API_URL to the backend origin, e.g. "https://api.example.com/api"
 * - Development: leave unset → falls back to "/api" (proxied by next.config.js rewrite)
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers as Record<string, string> ?? {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (res.status === 401) {
    removeToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ────────────────────────────────────────────────────────────────

export async function register(
  email: string,
  password: string,
  displayName: string,
  customerCode: string,
  authToken: string,
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName,
      customer_code: customerCode,
      auth_token: authToken,
    }),
  });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function mockLogin(): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/mock-login", { method: "POST" });
}

export async function getMe(): Promise<User> {
  return request<User>("/auth/me");
}

export async function updateProfile(data: {
  display_name?: string;
  customer_code?: string;
  auth_token?: string;
}): Promise<User> {
  return request<User>("/auth/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ── Chat ────────────────────────────────────────────────────────────────

export async function listSessions(): Promise<ChatSession[]> {
  return request<ChatSession[]>("/chat/sessions");
}

export async function getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  await request<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" });
}

/**
 * Stream chat response from the backend SSE endpoint.
 * Yields SSEEvent objects as they arrive.
 */
export async function* chatStream(
  message: string,
  sessionId?: string,
): AsyncGenerator<SSEEvent> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event: SSEEvent = JSON.parse(line.slice(6));
          yield event;
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}

