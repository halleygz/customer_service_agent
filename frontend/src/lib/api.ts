export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Order = {
  id: number;
  customer_id: number;
  product_name: string;
  order_status: string;
  total: string | number;
};

export type Subscription = {
  id: number;
  full_name: string;
  email: string;
  subscription_plan: string;
  account_status: string;
};

export type ConversationMessage = {
  message_role?: string;
  role?: string;
  message_content?: string;
  content?: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
};

export type ChatResponse = {
  conversation_id: string;
  customer_id: number;
  agent_response: string;
  selected_route: string;
  assigned_agent: string;
  status: string;
  handoff_note?: string | null;
  escalation_id?: number | null;
};

export type Escalation = {
  id: number;
  ticket_id: string;
  customer_id: number;
  full_name?: string;
  email?: string;
  subscription_plan?: string;
  route?: string;
  summary?: string;
  status: "open" | "in_progress" | "resolved";
  resolution_note?: string | null;
  assigned_admin?: string | null;
  linear_ticket_identifier?: string | null;
  linear_ticket_url?: string | null;
  created_at: string;
  updated_at: string;
  conversation?: ConversationMessage[];
  events?: Array<{ event_type: string; details: Record<string, unknown>; created_at: string }>;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchOrders(customerId: number) {
  return apiFetch<{ orders: Order[] }>(`/api/customer/${customerId}/orders`);
}

export async function fetchSubscription(customerId: number) {
  return apiFetch<{ subscription: Subscription }>(`/api/customer/${customerId}/subscription`);
}

export async function fetchConversation(conversationId: string) {
  return apiFetch<{ messages: ConversationMessage[] }>(`/api/conversations/${conversationId}/messages`);
}

export async function sendChatMessage(customerId: number, message: string, conversationId?: string | null) {
  return apiFetch<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ customer_id: customerId, message, conversation_id: conversationId }),
  });
}

export async function fetchEscalations() {
  return apiFetch<{ escalations: Escalation[] }>("/api/admin/escalations");
}

export async function fetchEscalationDetail(escalationId: number) {
  return apiFetch<{ escalation: Escalation }>(`/api/admin/escalations/${escalationId}`);
}

export async function sendHumanMessage(escalationId: number, message: string, sender = "human_agent") {
  return apiFetch<{ message: ConversationMessage }>(`/api/admin/escalations/${escalationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message, sender }),
  });
}

export async function updateEscalationStatus(
  escalationId: number,
  status: Escalation["status"],
  resolution_note?: string,
  assigned_admin?: string,
) {
  return apiFetch<{ escalation: Escalation }>(`/api/admin/escalations/${escalationId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, resolution_note, assigned_admin }),
  });
}

export async function verifyLinear() {
  return apiFetch<{ success: boolean; message?: string; viewer?: { email?: string }; team?: { key?: string; name?: string } }>(
    "/api/admin/linear/verify",
  );
}

export function messageRole(message: ConversationMessage) {
  return message.message_role || message.role || "unknown";
}

export function messageContent(message: ConversationMessage) {
  return message.message_content || message.content || "";
}
