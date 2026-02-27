export type ToolCall = {
  tool?: string;
  input?: Record<string, unknown>;
  output?: unknown;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  tool_calls?: ToolCall[];
};

export type SessionSummary = {
  session_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type LlmConfig = {
  model: string;
  base_url: string;
  api_key_set: boolean;
};

export type SkillSummary = {
  id: string;
  name: string;
  description: string;
  tags: string[];
};

