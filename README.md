# Customer Service Agent (LangGraph + Groq)

Phase 2 adds a Next.js web app, admin escalation dashboard, improved handoffs, escalation persistence, human-in-the-loop chat, and runtime observability.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run terminal experience:

```bash
python run.py
```

Run backend API:

```bash
python run_web.py
```

Run Next.js frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Customer UI: http://localhost:3000/
- Admin UI: http://localhost:3000/admin
- Backend API: http://localhost:8000/api/health

## Required Environment

- `GROQ_API_KEY`
- `GROQ_MODEL` (optional; defaults to `llama-3.3-70b-versatile`)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `LINEAR_API_KEY`
- `LINEAR_TEAM_ID` (team UUID or team key)
- `LINEAR_API_URL` (optional)
- `APP_LOG_LEVEL` (optional, default `INFO`)

## Key API Endpoints

Customer:

- `POST /api/chat`
- `GET /api/conversations/{conversation_id}/messages`
- `GET /api/customer/{customer_id}/orders`
- `GET /api/customer/{customer_id}/subscription`
- `GET /api/customer/{customer_id}/history`

Admin:

- `GET /api/admin/escalations`
- `GET /api/admin/escalations/{escalation_id}`
- `PATCH /api/admin/escalations/{escalation_id}`
- `POST /api/admin/escalations/{escalation_id}/messages`
- `GET /api/admin/linear/verify`


## Architecture overview

High level components:
- `app/graph` — LangGraph flow orchestrating context loading, classification, agent routing, tool usage, escalation, and persistence.
- `app/agents` — Agent implementations (supervisor triage, specialists, escalation agent).
- `app/tools` — Tool adapters that call services for DB mutations and Linear ticket creation.
- `app/services` — DB access, Linear API integration, LLM wrapper, orchestrator, and logging.
- `app/api` — Thin FastAPI API layer.
- `frontend` — Standalone Next.js customer portal and admin dashboard.

Design goals: centralize LLM usage (`app/services/llm.py`), separate tool adapters and service logic, persist conversation and escalation data, and enable agent-to-agent handoffs before human escalation.

### Agents and responsibilities

1. Supervisor (Triage) — `app/agents/supervisor.py`
- Performs structured classification on each incoming message. Output schema: `route`, `reason`, `confidence`, `requires_human`.
- Writes `selected_route` into state; records `previous_route` and `handoff_note` when route changes.

2. Billing Agent — `app/agents/specialists/billing.py`
- Handles order cancellations and subscription upgrades/downgrades.
- Calls tools: `manage_order` and `manage_subscription` (typed tool outputs).
- Escalates when automatic changes fail or when manual review is required.

3. Technical Support Agent — `app/agents/specialists/techincal.py`
- Provides troubleshooting steps and files bug tickets via `bug_report` when needed.

4. Feature Request Agent — `app/agents/specialists/feature.py`
- Collects feature request details and files a Linear issue via `request_feature`.

5. General Inquiry Agent — `app/agents/specialists/general.py`
- Uses the LLM to answer general product questions; default fallback when classification is weak.

6. Escalation Agent — `app/agents/escalation.py`
- Compiles a concise handoff summary and creates an escalation record in the DB (via `create_escalation`).
- Includes linked Linear ticket metadata when available.

### Tools and services

Tools (in `app/tools`) provide typed, deterministic adapters that call services:

- `customer_lookup` — fetches `customer` and `orders` via DB service.
- `manage_orders` — calls `database.cancel_order` and enforces ownership/cancellability.
- `manage_subscription` — calls `database.update_subscription` and validates transition.
- `req_feature` — files Linear feature request via `LinearService.createFeatureRequestTicket`.
- `bug_report` — files Linear bug ticket via `LinearService.createBugReportTicket`.

Services (in `app/services`):
- `database.py` — Postgres access, schema-creation helpers (conversation_messages, support_events, escalations), and CRUD helpers: `store_conversation_message`, `get_recent_conversation_history`, `store_support_event`, `create_escalation`, `list_escalations`, `get_escalation_detail`, `update_escalation_status`.
- `linear.py` — GraphQL wrapper for Linear, resolves team key or UUID, creates issues, and returns ticket metadata (id, identifier, url); exposes `verify_connection()`.
- `llm.py` — LLM wrapper (`llm_service`) supporting plain text, structured outputs, and a tool-calling entrypoint; falls back to deterministic heuristics if GROQ not configured.
- `orchestrator.py` — Turn-level orchestrator that prepares state and invokes the LangGraph graph; used by both terminal and API flows.
- `logger.py` — Centralized logger usage for readable, consistent runtime traces.

### LangGraph nodes and state

Primary nodes (see `app/graph/builder.py`):

- `load_customer_context` — loads profile and recent history.
- `classify_request` — supervisor triage node producing structured routing.
- `billing_agent`, `technical_support_agent`, `feature_request_agent`, `general_support_agent` — specialists.
- `escalation_agent` — human handoff node which creates an escalation record.
- `persist_interaction` — last step persisting messages, events, tool results, escalation metadata.

State fields (important):
- `conversation_id` / `ticket_id` — unique identifier for the session.
- `customer_id`, `customer_msg` — current turn payload.
- `customer_context` — snapshot of customer and orders.
- `conversation_history` — recent chat log used for prompts.
- `classification` — structured classifier output.
- `selected_route`, `previous_route`, `handoff_note` — routing/handoff metadata.
- `tool_results` — tool calls and responses.
- `requires_human`, `escalation_reason`, `escalation_id`, `support_summary`, `status` — escalation lifecycle.

Routing summary:
1. START → `load_customer_context`
2. `load_customer_context` → `classify_request`
3. `classify_request` → chosen specialist or `escalation_agent`
4. Specialist → if `requires_human` → `escalation_agent` else → `persist_interaction`
5. `escalation_agent` → `persist_interaction` → END

### Conversation lifecycle & handoffs

Per-turn flow:
1. Orchestrator prepares a state object for the turn (preserves `previous_route`).
2. Load customer data and recent history.
3. Supervisor returns structured route; system writes `handoff_note` if the route changed.
4. Specialist executes; may invoke tools and append results to `tool_results`.
5. If `requires_human` is set, escalation row is created and `escalation_id` recorded.
6. `persist_interaction` writes messages, tool events, and escalation events to DB.

Handoff policy: re-classify on every turn. If the intent changes to another AI-capable route, the graph hands off to that agent. Only escalate to human when a specialist sets `requires_human` or the user explicitly asks for a human.

### Running & verification

Install dependencies and run the terminal or web app.

Install:
```bash
pip install -r requirements.txt
```

Terminal prototype:
```bash
python run.py
```

Run backend API (FastAPI + Uvicorn):
```bash
python run_web.py
```

Run frontend UI (Next.js):
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000/ and http://localhost:3000/admin
```

Configure a non-default backend URL for the Next app:
```bash
cd frontend
cp .env.example .env.local
# edit NEXT_PUBLIC_API_BASE_URL if your API is not on http://localhost:8000
```


### Environment variables and configuration

Required for full integration:

- `GROQ_API_KEY` — Groq API key
- `GROQ_MODEL` — optional model name
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — Postgres connection
- `LINEAR_API_KEY` — Linear GraphQL auth header (usually `Bearer <token>`)
- `LINEAR_TEAM_ID` — Linear team key (e.g., `SIM`) or team UUID; the service resolves a key to UUID
- `APP_LOG_LEVEL` — optional (INFO, DEBUG)