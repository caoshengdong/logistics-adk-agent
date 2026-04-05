export interface User {
  id: string;
  email: string;
  display_name: string;
  customer_code: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResponse?: string;
  created_at: string;
}

export interface SSEEvent {
  type: "text" | "text_reset" | "done" | "tool_call" | "tool_result";
  content?: string;
  session_id?: string;
}

