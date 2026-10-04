import { Conversation, KbArticle, Message, PromptVersion, SystemSettings, User } from "../api/types";

export const MOCK_CURRENT_USER: User = {
  id: "usr_admin_1",
  email: "admin@company.com",
  name: "Sarah Jenkins (Lead)",
  role: "admin",
};

export const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "conv_1",
    wa_id_masked: "+1 (555) ••••• 8921",
    wa_id_full: "+15552348921",
    name: "Alex Morgan",
    status: "human",
    last_message_preview: "Can I talk to a real person? My package is missing.",
    last_user_msg_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 mins ago
    unread: 2,
  },
  {
    id: "conv_2",
    wa_id_masked: "+44 (791) ••••• 4310",
    wa_id_full: "+447911124310",
    name: "Marcus Vance",
    status: "bot",
    last_message_preview: "Your order *ORD-1029* is currently *In Transit* with FedEx.",
    last_user_msg_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    unread: 0,
  },
  {
    id: "conv_3",
    wa_id_masked: "+1 (415) ••••• 7762",
    wa_id_full: "+14159827762",
    name: "Elena Rostova",
    status: "human",
    last_message_preview: "Please cancel order ORD-2045 immediately.",
    last_user_msg_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 mins ago
    unread: 1,
  },
  {
    id: "conv_4",
    wa_id_masked: "+61 (400) ••••• 9134",
    wa_id_full: "+61400129134",
    name: "Liam O'Connor",
    status: "bot",
    last_message_preview: "I have booked your consultation for *Tomorrow at 10:00 AM*.",
    last_user_msg_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    unread: 0,
  },
  {
    id: "conv_5",
    wa_id_masked: "+1 (212) ••••• 3390",
    wa_id_full: "+12128913390",
    name: "David Kim",
    status: "closed",
    last_message_preview: "Thank you for the quick help!",
    last_user_msg_at: new Date(Date.now() - 32 * 60 * 60 * 1000).toISOString(), // >24h ago
    unread: 0,
  },
];

export const MOCK_MESSAGES: Record<string, Message[]> = {
  conv_1: [
    {
      id: "m_1_1",
      conversation_id: "conv_1",
      role: "user",
      content: "Hello, I placed an order three days ago and haven't received tracking yet.",
      created_at: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    },
    {
      id: "m_1_2",
      conversation_id: "conv_1",
      role: "bot",
      content: "Hello! I would be glad to check that for you. Could you please share your order number (e.g. *ORD-1029*)?",
      created_at: new Date(Date.now() - 24 * 60 * 1000).toISOString(),
    },
    {
      id: "m_1_3",
      conversation_id: "conv_1",
      role: "user",
      content: "Can I talk to a real person? My package is missing.",
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
    {
      id: "m_1_4",
      conversation_id: "conv_1",
      role: "bot",
      content: "I have flagged this conversation for a *human support agent*. A team member will respond here shortly.\n\n_Tip: Send *BOT* anytime to switch back to the AI assistant._",
      created_at: new Date(Date.now() - 14 * 60 * 1000).toISOString(),
    },
  ],
  conv_2: [
    {
      id: "m_2_1",
      conversation_id: "conv_2",
      role: "user",
      content: "Where is my order ORD-1029?",
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "m_2_2",
      conversation_id: "conv_2",
      role: "bot",
      content: "Your order *ORD-1029* is currently *In Transit* with FedEx.\n\n• *Tracking*: `TRK983726154`\n• *Estimated Delivery*: Tomorrow by 5:00 PM\n• *Items*: Wireless Noise-Cancelling Headphones (1x)",
      tool_calls: [
        {
          name: "check_order_status",
          status: "ok",
          args: { order_id: "ORD-1029" },
          result: { status: "In Transit", carrier: "FedEx", tracking_number: "TRK983726154" },
        },
      ],
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000 + 4000).toISOString(),
    },
  ],
  conv_3: [
    {
      id: "m_3_1",
      conversation_id: "conv_3",
      role: "user",
      content: "Please cancel order ORD-2045 immediately.",
      created_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    },
    {
      id: "m_3_2",
      conversation_id: "conv_3",
      role: "bot",
      content: "Canceling an order is an irreversible action. Order *ORD-2045* is currently processing for $89.50.\n\nAre you sure you want to cancel this order? Reply *CONFIRM* to proceed.",
      tool_calls: [
        {
          name: "cancel_order",
          status: "requires_user_confirmation",
          args: { order_id: "ORD-2045" },
        },
      ],
      created_at: new Date(Date.now() - 44 * 60 * 1000).toISOString(),
    },
  ],
  conv_4: [
    {
      id: "m_4_1",
      conversation_id: "conv_4",
      role: "user",
      content: "Hi! Can I schedule a call with your sales team for tomorrow at 10 AM?",
      created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "m_4_2",
      conversation_id: "conv_4",
      role: "bot",
      content: "I have booked your consultation for *Tomorrow at 10:00 AM*!\n\n• *Reference ID*: `APT-8821`\n• *Topic*: General Inquiry\n\nWe will send a reminder 1 hour prior.",
      tool_calls: [
        {
          name: "schedule_appointment",
          status: "ok",
          args: { date: "Tomorrow", time_slot: "10:00 AM" },
        },
      ],
      created_at: new Date(Date.now() - 6 * 60 * 60 * 1000 + 3000).toISOString(),
    },
  ],
  conv_5: [
    {
      id: "m_5_1",
      conversation_id: "conv_5",
      role: "user",
      content: "What is your return policy?",
      created_at: new Date(Date.now() - 33 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "m_5_2",
      conversation_id: "conv_5",
      role: "bot",
      content: "We offer a *30-day no-questions-asked return policy* on all unused items in original packaging with prepaid return labels.",
      created_at: new Date(Date.now() - 33 * 60 * 60 * 1000 + 2000).toISOString(),
    },
    {
      id: "m_5_3",
      conversation_id: "conv_5",
      role: "user",
      content: "Thank you for the quick help!",
      created_at: new Date(Date.now() - 32 * 60 * 60 * 1000).toISOString(),
    },
  ],
};

export const MOCK_KB_ARTICLES: KbArticle[] = [
  {
    id: "kb_1",
    title: "Operating Hours & Customer Support",
    key: "hours",
    content: "Our customer support team is available Monday through Friday from 9:00 AM to 6:00 PM EST. Automated bot support runs 24/7.",
    tags: ["general", "support", "hours"],
    updated_at: "2026-09-15T10:00:00Z",
  },
  {
    id: "kb_2",
    title: "Return and Exchange Policy",
    key: "return",
    content: "We offer a 30-day return policy for unused items in original packaging. Refunds are processed to original payment method within 3-5 business days of receipt.",
    tags: ["returns", "policy", "refunds"],
    updated_at: "2026-09-20T14:30:00Z",
  },
  {
    id: "kb_3",
    title: "Shipping Times and Express Options",
    key: "shipping",
    content: "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days. Orders over $50 qualify for free standard delivery.",
    tags: ["shipping", "delivery", "rates"],
    updated_at: "2026-09-28T09:15:00Z",
  },
  {
    id: "kb_4",
    title: "Hardware Limited Warranty",
    key: "warranty",
    content: "All electronics and mechanical accessories include a 1-year limited warranty covering manufacturer defects and mechanical component failures.",
    tags: ["warranty", "repairs", "coverage"],
    updated_at: "2026-10-01T11:20:00Z",
  },
];

export const MOCK_SYSTEM_SETTINGS: SystemSettings = {
  system_prompt: `You are an intelligent, helpful, and concise customer support AI agent communicating with users on WhatsApp for our business.

CRITICAL WHATSAPP FORMATTING RULES:
1. WhatsApp DOES NOT support Markdown headings (# Heading), HTML tags, or Markdown tables (| col |). NEVER use them.
2. WhatsApp only supports: *bold*, _italics_, ~strikethrough~, and \`\`\`monospace\`\`\`.
3. Keep answers clean, friendly, and easily scannable for mobile screens. Use bullet points with emojis or hyphens rather than long paragraphs.
4. Keep replies within standard conversational lengths.
5. If the user asks about an order, appointments, or policies, use the available tools to provide real, accurate details.
6. SAFETY RULE: Actions with irreversible side effects (cancellations, refunds, payments) require explicit confirmation before execution.`,
  model: "claude-3-5-sonnet-latest",
  rate_limit_per_min: 10,
  max_history_turns: 20,
  handoff_keywords: ["agent", "human", "support", "representative", "helpdesk"],
  opt_out_keywords: ["stop", "unsubscribe", "cancel", "opt out"],
};

export const MOCK_PROMPT_VERSIONS: PromptVersion[] = [
  {
    id: "v3",
    created_at: "2026-10-02T16:00:00Z",
    created_by: "Sarah Jenkins",
    summary: "Add strict confirmation rule for refunds & cancellations",
    prompt: MOCK_SYSTEM_SETTINGS.system_prompt,
  },
  {
    id: "v2",
    created_at: "2026-09-18T11:30:00Z",
    created_by: "Alex Chen",
    summary: "Refine WhatsApp markdown guidelines and forbid HTML headers",
    prompt: `You are a helpful customer support AI agent on WhatsApp.
Never use markdown headers or markdown tables because WhatsApp cannot display them.
Use *bold* and _italics_ instead.`,
  },
  {
    id: "v1",
    created_at: "2026-09-01T09:00:00Z",
    created_by: "Sarah Jenkins",
    summary: "Initial baseline prompt for customer support bot",
    prompt: `You are a customer support bot on WhatsApp. Answer customer inquiries politely and concisely.`,
  },
];
