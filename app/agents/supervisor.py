from typing import Literal

from pydantic import BaseModel, Field

from app.services.llm import llm_service


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

	requires_human = bool(result.requires_human or result.confidence < 0.55)
	selected_route = "escalation" if requires_human else result.route

	return {
		"classification": result.model_dump(),
		"selected_route": selected_route,
		"requires_human": requires_human,
		"escalation_reason": (
			result.reason
			if selected_route == "escalation"
			else state.get("escalation_reason")
		),
	}
