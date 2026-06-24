"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ChatResponse,
  ConversationMessage,
  Order,
  Subscription,
  fetchConversation,
  fetchOrders,
  fetchSubscription,
  messageContent,
  messageRole,
  sendChatMessage,
} from "@/lib/api";

function formatCurrency(value: string | number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `$${parsed.toFixed(2)}` : String(value);
}

function roleLabel(role: string) {
  if (role === "human_agent") return "Human Support";
  if (role === "agent") return "AI Agent";
  if (role === "customer") return "You";
  return role.replaceAll("_", " ");
}

export default function CustomerPortal() {
  const [customerId, setCustomerId] = useState(1);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const storageKey = useMemo(() => `cs-agent-conversation-${customerId}`, [customerId]);

  async function loadCustomerData(activeConversationId = conversationId) {
    setError(null);
    try {
      const [ordersPayload, subscriptionPayload] = await Promise.all([
        fetchOrders(customerId),
        fetchSubscription(customerId),
      ]);
      setOrders(ordersPayload.orders);
      setSubscription(subscriptionPayload.subscription);

      if (activeConversationId) {
        const conversation = await fetchConversation(activeConversationId);
        setMessages(conversation.messages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load customer data");
    }
  }

  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    const id = stored || `cust-${customerId}`;
    setConversationId(id);
    void loadCustomerData(id);
  }, [customerId]);

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setMessages((current) => [...current, { role: "customer", content: trimmed }]);
    setMessage("");

    try {
      const response = await sendChatMessage(customerId, trimmed, conversationId);
      setLastResponse(response);
      setConversationId(response.conversation_id);
      window.localStorage.setItem(storageKey, response.conversation_id);
      await loadCustomerData(response.conversation_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!conversationId || lastResponse?.assigned_agent !== "human_support") return;
    const interval = window.setInterval(() => {
      void fetchConversation(conversationId).then((payload) => setMessages(payload.messages));
    }, 4000);
    return () => window.clearInterval(interval);
  }, [conversationId, lastResponse?.assigned_agent]);

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <div className="eyebrow">Customer Portal</div>
          <h1>Support that knows the whole story.</h1>
          <p>Chat with the LangGraph support agent, review order state, and see subscription changes update from the database.</p>
        </div>
        <Link className="nav-link" href="/admin">Admin dashboard</Link>
      </header>

      <section className="grid customer">
        <div className="card">
          <div className="form-row" style={{ marginBottom: "1rem" }}>
            <input
              type="number"
              min="1"
              value={customerId}
              onChange={(event) => setCustomerId(Number(event.target.value) || 1)}
              aria-label="Customer ID"
            />
            <button className="secondary" type="button" onClick={() => loadCustomerData()}>
              Reload customer
            </button>
          </div>

          <div className="chat-window" aria-live="polite">
            {messages.length === 0 ? (
              <p className="muted">Start a conversation with the support agent.</p>
            ) : (
              messages.map((item, index) => {
                const role = messageRole(item);
                return (
                  <div className={`message ${role}`} key={`${item.created_at || "draft"}-${index}`}>
                    <span className="role">{roleLabel(role)}</span>
                    <span>{messageContent(item)}</span>
                  </div>
                );
              })
            )}
          </div>

          <form onSubmit={handleSend} className="form-row" style={{ marginTop: "1rem" }}>
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask to cancel an order, change subscription, report a bug, or request a human..."
            />
            <button type="submit" disabled={loading}>{loading ? "Sending..." : "Send"}</button>
          </form>

          {lastResponse && (
            <p className="muted">
              Route: <strong>{lastResponse.selected_route}</strong> | Handler: <strong>{lastResponse.assigned_agent}</strong> | Status: <strong>{lastResponse.status}</strong>
              {lastResponse.handoff_note ? ` | ${lastResponse.handoff_note}` : ""}
            </p>
          )}
          {error && <p className="error">{error}</p>}
        </div>

        <aside className="panel-stack">
          <section className="card tight">
            <h2>Subscription</h2>
            {subscription ? (
              <div className="meta-grid" style={{ marginTop: "1rem" }}>
                <div className="meta-box"><strong>Name</strong>{subscription.full_name}</div>
                <div className="meta-box"><strong>Status</strong>{subscription.account_status}</div>
                <div className="meta-box"><strong>Plan</strong>{subscription.subscription_plan}</div>
                <div className="meta-box"><strong>Email</strong>{subscription.email}</div>
              </div>
            ) : <p className="muted">No subscription loaded.</p>}
          </section>

          <section className="card tight">
            <h2>Orders</h2>
            <div className="table-wrap">
              <table>
                <thead><tr><th>ID</th><th>Product</th><th>Status</th><th>Total</th></tr></thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td>{order.id}</td>
                      <td>{order.product_name}</td>
                      <td><span className="status-pill">{order.order_status}</span></td>
                      <td>{formatCurrency(order.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
