/** Shared API types for WhatsApp AI Agent Admin Dashboard */

export type Role = "user" | "bot" | "staff";
export type ConvStatus = "bot" | "human" | "closed";
export type StaffRole = "admin" | "agent";

export interface MessageMedia {
  type: "image" | "audio";
  url: string;
  caption?: string;
}

export interface ToolCallItem {
  name: string;
  status: "ok" | "error" | "requires_user_confirmation";
  args?: Record<string, any>;
  result?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: Role;
  content: string;
  media?: MessageMedia;
  tool_calls?: ToolCallItem[];
  created_at: string;
  pending?: boolean;
  failed?: boolean;
}

export interface Conversation {
  id: string;
  wa_id_masked: string;
  wa_id_full?: string;
  name?: string;
  status: ConvStatus;
  last_message_preview: string;
  last_user_msg_at: string;
  unread: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: StaffRole;
}

export interface KbArticle {
  id: string;
  title: string;
  key: string;
  content: string;
  tags: string[];
  updated_at: string;
}

export interface SystemSettings {
  system_prompt: string;
  model: string;
  rate_limit_per_min: number;
  max_history_turns: number;
  handoff_keywords: string[];
  opt_out_keywords: string[];
}

export interface PromptVersion {
  id: string;
  prompt: string;
  created_at: string;
  created_by: string;
  summary: string;
}

export interface AnalyticsStats {
  total_conversations: number;
  messages_today: number;
  handoff_rate: number;
  avg_response_time_sec: number;
  bot_resolution_rate: number;
  estimated_token_cost_usd: number;
  daily_volume: { date: string; user_messages: number; bot_replies: number }[];
}
