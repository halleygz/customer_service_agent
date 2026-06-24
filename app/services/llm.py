import os
import re
from typing import Any, Dict, List, Type

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from pydantic import BaseModel

load_dotenv()


def _heuristic_route(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    asks_human = any(token in lowered for token in ["human", "person", "representative", "agent"])
    if asks_human and any(token in lowered for token in ["talk", "speak", "connect", "escalate"]):
        return {
            "route": "escalation",
            "reason": "Customer explicitly asked for a human.",
            "confidence": 0.98,
            "requires_human": True,
        }

    if any(token in lowered for token in ["cancel order", "order", "billing", "charge", "refund", "subscription", "plan"]):
        return {
            "route": "billing",
            "reason": "Message contains billing or order signals.",
            "confidence": 0.85,
            "requires_human": False,
        }

    if any(token in lowered for token in ["feature", "would like", "please add", "enhancement"]):
        return {
            "route": "feature_request",
            "reason": "Message requests a product enhancement.",
            "confidence": 0.84,
            "requires_human": False,
        }

    if any(token in lowered for token in ["bug", "error", "broken", "crash", "not working", "fails"]):
        return {
            "route": "technical_support",
            "reason": "Message contains technical issue keywords.",
            "confidence": 0.83,
            "requires_human": False,
        }

    return {
        "route": "general_inquiry",
        "reason": "No stronger specialty signals detected.",
        "confidence": 0.65,
        "requires_human": False,
    }


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self._model = None
        self.mock_mode = not bool(api_key)

        if self.mock_mode:
            print("Warning: GROQ_API_KEY not set. Running in deterministic fallback mode.")
            return

        try:
            self._model = ChatGroq(
                api_key=api_key,
                model_name=model_name,
                temperature=0.2,
            )
        except Exception as exc:
            print(f"Warning: failed to initialize Groq model ({exc}). Using fallback mode.")
            self.mock_mode = True

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.mock_mode or not self._model:
            return (
                "I reviewed your request and customer context. "
                "I can help with billing, technical support, feature requests, and general questions."
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = self._model.invoke(messages)
            return response.content if isinstance(response.content, str) else str(response.content)
        except Exception:
            return (
                "I reviewed your request, but I hit a temporary model error. "
                "I will continue using deterministic fallback handling."
            )

    def invoke_structured(
        self,
        schema: Type[BaseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> BaseModel:
        if self.mock_mode or not self._model:
            return schema.model_validate(_heuristic_route(user_prompt))

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            structured_model = self._model.with_structured_output(schema)
            return structured_model.invoke(messages)
        except Exception:
            # Fallback to deterministic routing if structured call fails.
            return schema.model_validate(_heuristic_route(user_prompt))

    def extract_order_id(self, message: str) -> int | None:
        match = re.search(r"order\s*#?\s*(\d+)", message, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_target_plan(self, message: str) -> str | None:
        lowered = message.lower()
        for plan in ["enterprise", "premium", "free"]:
            if plan in lowered:
                return plan.title()
        return None

    def invoke_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[BaseTool],
    ):
        if self.mock_mode or not self._model:
            return {
                "content": "Tool-calling mock mode: no model tool call emitted.",
                "tool_calls": [],
            }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            return self._model.bind_tools(tools).invoke(messages)
        except Exception:
            return {
                "content": "Tool-calling failed at model layer.",
                "tool_calls": [],
            }


llm_service = LLMService()
