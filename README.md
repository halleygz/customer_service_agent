# Customer Service Agent (LangGraph + Groq)

Phase 2 adds a web app, admin escalation dashboard, improved handoffs, escalation persistence, and runtime observability.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run terminal experience:

```bash
python run.py
```

Run web app + admin dashboard:

```bash
python run_web.py
```

Open:

- Customer UI: http://localhost:8000/
- Admin UI: http://localhost:8000/admin

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
- `GET /api/customer/{customer_id}/orders`
- `GET /api/customer/{customer_id}/subscription`
- `GET /api/customer/{customer_id}/history`

Admin:

- `GET /api/admin/escalations`
- `GET /api/admin/escalations/{escalation_id}`
- `PATCH /api/admin/escalations/{escalation_id}`
- `GET /api/admin/linear/verify`
