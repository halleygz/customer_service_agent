"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Escalation,
  fetchEscalationDetail,
  fetchEscalations,
  messageContent,
  messageRole,
  sendHumanMessage,
  updateEscalationStatus,
  verifyLinear,
} from "@/lib/api";

function roleLabel(role: string) {
  if (role === "human_agent") return "Human Support";
  if (role === "agent") return "AI Agent";
  if (role === "customer") return "Customer";
  return role.replaceAll("_", " ");
}

export default function AdminDashboard() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<Escalation | null>(null);
  const [reply, setReply] = useState("");
  const [resolutionNote, setResolutionNote] = useState("");
  const [assignedAdmin, setAssignedAdmin] = useState("human_agent");
  const [status, setStatus] = useState<Escalation["status"]>("open");
  const [linearStatus, setLinearStatus] = useState("Checking Linear...");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selectedEscalation = useMemo(
    () => escalations.find((item) => item.id === selectedId) || null,
    [escalations, selectedId],
  );

  async function loadEscalations() {
    const payload = await fetchEscalations();
    setEscalations(payload.escalations);
    if (!selectedId && payload.escalations.length > 0) {
      setSelectedId(payload.escalations[0].id);
    }
  }

  async function loadDetail(escalationId: number) {
    const payload = await fetchEscalationDetail(escalationId);
    setDetail(payload.escalation);
    setStatus(payload.escalation.status);
    setAssignedAdmin(payload.escalation.assigned_admin || "human_agent");
    setResolutionNote(payload.escalation.resolution_note || "");
  }

  async function handleReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !reply.trim()) return;

    setBusy(true);
    setError(null);
    try {
      await sendHumanMessage(selectedId, reply.trim(), assignedAdmin || "human_agent");
      setReply("");
      await Promise.all([loadDetail(selectedId), loadEscalations()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send human reply");
    } finally {
      setBusy(false);
    }
  }

  async function handleStatusUpdate() {
    if (!selectedId) return;

    setBusy(true);
    setError(null);
    try {
      await updateEscalationStatus(selectedId, status, resolutionNote || undefined, assignedAdmin || undefined);
      await Promise.all([loadDetail(selectedId), loadEscalations()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update escalation");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadEscalations().catch((err) => setError(err instanceof Error ? err.message : "Failed to load escalations"));
    void verifyLinear()
      .then((payload) => {
        setLinearStatus(payload.success
          ? `Linear connected${payload.team?.key ? ` (${payload.team.key})` : ""}`
          : payload.message || "Linear verification failed");
      })
      .catch((err) => setLinearStatus(err instanceof Error ? err.message : "Linear verification failed"));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    void loadDetail(selectedId).catch((err) => setError(err instanceof Error ? err.message : "Failed to load detail"));
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    const interval = window.setInterval(() => {
      void loadDetail(selectedId);
      void loadEscalations();
    }, 5000);
    return () => window.clearInterval(interval);
  }, [selectedId]);

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <div className="eyebrow">Human-in-the-loop</div>
          <h1>Escalation command center.</h1>
          <p>Pick an escalated case, read the AI handoff, and reply directly to the customer's support thread.</p>
        </div>
        <Link className="nav-link" href="/">Customer portal</Link>
      </header>

      <section className="grid admin">
        <aside className="card">
          <div className="form-row" style={{ justifyContent: "space-between", marginBottom: "1rem" }}>
            <h2>Escalations</h2>
            <button className="secondary" type="button" onClick={() => loadEscalations()}>Refresh</button>
          </div>
          <p className={linearStatus.startsWith("Linear connected") ? "success-text" : "muted"}>{linearStatus}</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Customer</th><th>Status</th><th>Linear</th></tr></thead>
              <tbody>
                {escalations.map((item) => (
                  <tr
                    key={item.id}
                    className="clickable"
                    onClick={() => setSelectedId(item.id)}
                    style={{ background: item.id === selectedId ? "rgba(12,93,165,0.11)" : undefined }}
                  >
                    <td>{item.id}</td>
                    <td>{item.full_name || `Customer ${item.customer_id}`}<br /><span className="muted">{item.route || "route unknown"}</span></td>
                    <td><span className="status-pill">{item.status}</span></td>
                    <td>{item.linear_ticket_identifier || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </aside>

        <section className="panel-stack">
          <div className="card">
            <h2>Case detail</h2>
            {!detail ? (
              <p className="muted">Select an escalation to inspect the support thread.</p>
            ) : (
              <>
                <div className="meta-grid" style={{ margin: "1rem 0" }}>
                  <div className="meta-box"><strong>Escalation</strong>#{detail.id}</div>
                  <div className="meta-box"><strong>Customer</strong>{detail.full_name || detail.customer_id}</div>
                  <div className="meta-box"><strong>Route</strong>{detail.route || "unknown"}</div>
                  <div className="meta-box"><strong>Ticket</strong>{detail.linear_ticket_identifier || "No Linear ticket"}</div>
                </div>
                <h3>AI handoff summary</h3>
                <p>{detail.summary}</p>
              </>
            )}
          </div>

          <div className="card">
            <h2>Live support thread</h2>
            <div className="chat-window" style={{ minHeight: 320 }}>
              {(detail?.conversation || []).length === 0 ? (
                <p className="muted">No messages yet.</p>
              ) : detail?.conversation?.map((item, index) => {
                const role = messageRole(item);
                return (
                  <div className={`message ${role}`} key={`${item.created_at || "msg"}-${index}`}>
                    <span className="role">{roleLabel(role)}</span>
                    <span>{messageContent(item)}</span>
                  </div>
                );
              })}
            </div>

            <form onSubmit={handleReply} className="panel-stack" style={{ marginTop: "1rem" }}>
              <input
                value={assignedAdmin}
                onChange={(event) => setAssignedAdmin(event.target.value)}
                placeholder="Agent display name"
              />
              <textarea
                rows={3}
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                placeholder="Type a human reply to the customer..."
              />
              <button type="submit" disabled={!selectedId || busy}>{busy ? "Sending..." : "Send human reply"}</button>
            </form>
          </div>

          <div className="card">
            <h2>Resolution workflow</h2>
            <div className="form-row" style={{ marginTop: "1rem" }}>
              <select value={status} onChange={(event) => setStatus(event.target.value as Escalation["status"])}>
                <option value="open">open</option>
                <option value="in_progress">in_progress</option>
                <option value="resolved">resolved</option>
              </select>
              <button className="success" type="button" disabled={!selectedId || busy} onClick={handleStatusUpdate}>Update status</button>
            </div>
            <textarea
              rows={3}
              style={{ marginTop: "0.8rem" }}
              value={resolutionNote}
              onChange={(event) => setResolutionNote(event.target.value)}
              placeholder="Resolution note"
            />
            {error && <p className="error">{error}</p>}
          </div>
        </section>
      </section>
    </main>
  );
}
