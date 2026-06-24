from pathlib import Path
from typing import Dict, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.database import (
    get_customer_orders,
    get_customer_subscription,
    get_recent_conversation_history,
    get_escalation_detail,
    list_escalations,
    update_escalation_status,
)
from app.services.linear import LinearService
from app.services.logger import get_logger
from app.services.orchestrator import create_initial_state, run_customer_turn


logger = get_logger("api")
app = FastAPI(title="Customer Support System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
static_dir = frontend_dir / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

SESSION_STATES: Dict[str, Dict] = {}


class ChatRequest(BaseModel):
    customer_id: int
    message: str = Field(min_length=1)
    conversation_id: Optional[str] = None


class EscalationUpdateRequest(BaseModel):
    status: Literal["open", "in_progress", "resolved"]
    resolution_note: Optional[str] = None
    assigned_admin: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def customer_page():
    with open(frontend_dir / "templates" / "customer.html", "r", encoding="utf-8") as file:
        return file.read()


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    with open(frontend_dir / "templates" / "admin.html", "r", encoding="utf-8") as file:
        return file.read()


@app.post("/api/chat")
def send_chat_message(payload: ChatRequest):
    conversation_id = payload.conversation_id or f"cust-{payload.customer_id}"

    state = SESSION_STATES.get(conversation_id)
    if not state:
        state = create_initial_state(customer_id=payload.customer_id, conversation_id=conversation_id)

    try:
        result = run_customer_turn(state, payload.message)
    except Exception as exc:
        logger.exception("chat_processing_failed conversation_id=%s", conversation_id)
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {exc}") from exc

    SESSION_STATES[conversation_id] = result

    return {
        "conversation_id": result.get("conversation_id", conversation_id),
        "customer_id": result.get("customer_id"),
        "agent_response": result.get("agent_response"),
        "selected_route": result.get("selected_route"),
        "assigned_agent": result.get("assigned_agent"),
        "status": result.get("status"),
        "handoff_note": result.get("handoff_note"),
        "escalation_id": result.get("escalation_id"),
    }


@app.get("/api/customer/{customer_id}/orders")
def customer_orders(customer_id: int):
    return {"orders": get_customer_orders(customer_id)}


@app.get("/api/customer/{customer_id}/subscription")
def customer_subscription(customer_id: int):
    subscription = get_customer_subscription(customer_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"subscription": subscription}


@app.get("/api/customer/{customer_id}/history")
def customer_history(customer_id: int, limit: int = 25):
    return {"history": get_recent_conversation_history(customer_id, limit=limit)}


@app.get("/api/admin/escalations")
def admin_list_escalations():
    return {"escalations": list_escalations()}


@app.get("/api/admin/escalations/{escalation_id}")
def admin_escalation_detail(escalation_id: int):
    detail = get_escalation_detail(escalation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return {"escalation": detail}


@app.patch("/api/admin/escalations/{escalation_id}")
def admin_update_escalation(escalation_id: int, payload: EscalationUpdateRequest):
    updated = update_escalation_status(
        escalation_id=escalation_id,
        status=payload.status,
        resolution_note=payload.resolution_note,
        assigned_admin=payload.assigned_admin,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return {"escalation": updated}


@app.get("/api/admin/linear/verify")
def admin_verify_linear():
    linear = LinearService()
    return linear.verify_connection()
