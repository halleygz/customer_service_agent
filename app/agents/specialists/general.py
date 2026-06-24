from app.services.llm import llm_service
from app.utils.format_history import format_conversation_history


GENERAL_SYSTEM_PROMPT = """
You are a professional customer support assistant.
Answer clearly and concisely for general questions.
If unsure, provide the best safe guidance and suggest escalation.
""".strip()


def general_support_agent(state):
    history_text = format_conversation_history(state.get("conversation_history", []))
    user_prompt = (
        f"Customer context:\n{state.get('customer_context')}\n\n"
        f"Conversation history:\n{history_text}\n\n"
        f"Current message:\n{state.get('customer_msg', '')}"
    )
    response = llm_service.invoke_text(GENERAL_SYSTEM_PROMPT, user_prompt)

    return {
        "assigned_agent": "general_inquiry",
        "agent_response": response,
        "tool_results": state.get("tool_results", []),
        "status": "resolved",
    }