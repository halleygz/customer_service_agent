from typing import Literal

from pydantic import BaseModel, Field

from app.services.logger import get_logger
from app.services.llm import llm_service


logger = get_logger("supervisor")


class RoutingDecisionModel(BaseModel):
	route: Literal[
		"billing",
		"technical_support",
		"feature_request",
		"general_inquiry",
		"escalation",
	] = Field(description="Best route for the current customer request")
	reason: str = Field(description="Short reason for routing decision")
	confidence: float = Field(ge=0.0, le=1.0)
	requires_human: bool = False


CLASSIFIER_SYSTEM_PROMPT = """
You are a customer-support triage router.
Return ONLY structured routing output.

Valid routes:
- billing
- technical_support
- feature_request
- general_inquiry
- escalation

Routing rules:
- Route to escalation if the customer asks for a human or live representative.
- If confidence is below 0.55, set requires_human=true.
- Keep reasons concise and factual.
""".strip()


def classify_request(state):
	customer_msg = state.get("customer_msg", "")
	result = llm_service.invoke_structured(
		schema=RoutingDecisionModel,
		system_prompt=CLASSIFIER_SYSTEM_PROMPT,
		user_prompt=customer_msg,
	)

	message_lower = customer_msg.lower()
	explicit_human_request = any(token in message_lower for token in ["human", "representative", "live agent"]) and any(
		token in message_lower for token in ["talk", "speak", "connect", "escalate"]
	)

	selected_route = result.route
	requires_human = bool(result.requires_human and explicit_human_request)
	if explicit_human_request:
		selected_route = "escalation"
		requires_human = True
	elif result.confidence < 0.55:
		# Low confidence defaults to general inquiry first to allow AI handoff before human escalation.
		selected_route = "general_inquiry"
		requires_human = False

	previous_route = state.get("selected_route")
	handoff_note = None
	if previous_route and previous_route != selected_route:
		handoff_note = f"Handoff from {previous_route} to {selected_route}"

	logger.info(
		"classifier_decision route=%s confidence=%.2f requires_human=%s reason=%s",
		selected_route,
		result.confidence,
		requires_human,
		result.reason,
	)

	return {
		"classification": result.model_dump(),
		"selected_route": selected_route,
		"previous_route": previous_route,
		"handoff_note": handoff_note,
		"requires_human": requires_human,
		"escalation_reason": (
			result.reason
			if selected_route == "escalation"
			else None
		),
	}
