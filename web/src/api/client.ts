/**
 * API client wrapper with credentials, typed errors, and mock fallback.
 */

import { MOCK_CONVERSATIONS, MOCK_CURRENT_USER, MOCK_KB_ARTICLES, MOCK_MESSAGES, MOCK_PROMPT_VERSIONS, MOCK_SYSTEM_SETTINGS } from "../mocks/data";
import { Message, User } from "./types";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL || "";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false";

// In-memory mock state for dev/demo mode
let mockConversations = [...MOCK_CONVERSATIONS];
let mockMessages = { ...MOCK_MESSAGES };
let mockSettings = { ...MOCK_SYSTEM_SETTINGS };
let mockKb = [...MOCK_KB_ARTICLES];
let mockPromptVersions = [...MOCK_PROMPT_VERSIONS];
let currentUser: User | null = MOCK_CURRENT_USER;

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  // If USE_MOCKS is enabled and backend is not explicitly requested, handle via mock store
  if (USE_MOCKS) {
    return handleMockRequest<T>(endpoint, options);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "include",
    });

    if (response.status === 401) {
      // Unauthorized: redirect to login
      if (window.location.pathname !== "/login") {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
      throw new ApiError(401, "Session expired or unauthorized");
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = await response.text();
      }
      throw new ApiError(response.status, errorData?.detail || response.statusText, errorData);
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(500, err.message || "Network request failed");
  }
}

// Simulates backend responses with small natural latency
async function handleMockRequest<T>(endpoint: string, options: RequestInit): Promise<T> {
  await new Promise((r) => setTimeout(r, 80)); // Simulate 80ms latency

  const method = options.method || "GET";
  const body = options.body ? JSON.parse(options.body as string) : {};

  // Auth routes
  if (endpoint === "/auth/me") {
    if (!currentUser) throw new ApiError(401, "Not authenticated");
    return currentUser as T;
  }

  if (endpoint === "/auth/login" && method === "POST") {
    const { email } = body;
    currentUser = {
      id: "usr_1",
      email: email || "admin@company.com",
      name: email?.includes("agent") ? "Alex Support" : "Sarah Jenkins (Lead)",
      role: email?.includes("agent") ? "agent" : "admin",
    };
    return { success: true, user: currentUser } as T;
  }

  if (endpoint === "/auth/logout" && method === "POST") {
    currentUser = null;
    return { success: true } as T;
  }

  // Conversations list
  if (endpoint.startsWith("/conversations") && !endpoint.includes("/messages") && method === "GET") {
    return {
      items: mockConversations,
      next_cursor: null,
    } as T;
  }

  // Conversation thread messages
  const msgMatch = endpoint.match(/\/conversations\/([^/]+)\/messages/);
  if (msgMatch && method === "GET") {
    const convId = msgMatch[1];
    return {
      items: mockMessages[convId] || [],
      next_cursor: null,
    } as T;
  }

  // Takeover conversation
  const takeoverMatch = endpoint.match(/\/conversations\/([^/]+)\/takeover/);
  if (takeoverMatch && method === "POST") {
    const convId = takeoverMatch[1];
    mockConversations = mockConversations.map((c) =>
      c.id === convId ? { ...c, status: "human" } : c
    );
    return { status: "human", success: true } as T;
  }

  // Release conversation back to bot
  const releaseMatch = endpoint.match(/\/conversations\/([^/]+)\/release/);
  if (releaseMatch && method === "POST") {
    const convId = releaseMatch[1];
    mockConversations = mockConversations.map((c) =>
      c.id === convId ? { ...c, status: "bot" } : c
    );
    return { status: "bot", success: true } as T;
  }

  // Send message from staff
  const sendMatch = endpoint.match(/\/conversations\/([^/]+)\/send/);
  if (sendMatch && method === "POST") {
    const convId = sendMatch[1];
    const newMsg: Message = {
      id: `m_staff_${Date.now()}`,
      conversation_id: convId,
      role: "staff",
      content: body.content,
      created_at: new Date().toISOString(),
    };
    mockMessages[convId] = [...(mockMessages[convId] || []), newMsg];
    // Update conversation last message preview
    mockConversations = mockConversations.map((c) =>
      c.id === convId
        ? {
            ...c,
            last_message_preview: body.content,
            unread: 0,
          }
        : c
    );
    return newMsg as T;
  }

  // KB Articles
  if (endpoint === "/kb" && method === "GET") {
    return mockKb as T;
  }
  if (endpoint === "/kb" && method === "POST") {
    const newArticle = {
      id: `kb_${Date.now()}`,
      title: body.title || "Untitled Article",
      key: body.key || "custom_key",
      content: body.content || "",
      tags: body.tags || [],
      updated_at: new Date().toISOString(),
    };
    mockKb.push(newArticle);
    return newArticle as T;
  }
  if (endpoint.startsWith("/kb/") && method === "PUT") {
    const kbId = endpoint.split("/kb/")[1];
    mockKb = mockKb.map((a) =>
      a.id === kbId ? { ...a, ...body, updated_at: new Date().toISOString() } : a
    );
    return { success: true } as T;
  }
  if (endpoint.startsWith("/kb/") && method === "DELETE") {
    const kbId = endpoint.split("/kb/")[1];
    mockKb = mockKb.filter((a) => a.id !== kbId);
    return { success: true } as T;
  }

  // System Settings
  if (endpoint === "/settings" && method === "GET") {
    return mockSettings as T;
  }
  if (endpoint === "/settings" && (method === "PUT" || method === "POST")) {
    mockSettings = { ...mockSettings, ...body };
    if (body.system_prompt && body.system_prompt !== mockPromptVersions[0]?.prompt) {
      mockPromptVersions.unshift({
        id: `v${mockPromptVersions.length + 1}`,
        prompt: body.system_prompt,
        created_at: new Date().toISOString(),
        created_by: currentUser?.name || "Staff Admin",
        summary: body.version_summary || "Prompt updated from admin dashboard",
      });
    }
    return mockSettings as T;
  }

  // Prompt History
  if (endpoint === "/settings/prompt-history" && method === "GET") {
    return mockPromptVersions as T;
  }

  throw new ApiError(404, `Not found: ${endpoint}`);
}
