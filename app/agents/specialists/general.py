from app.utils.format_history import format_conversation_history
from services.llm import llm

from prompts.general import (
    GENERAL_SUPPORT_PROMPT
)


def general_support_agent(state):
    """Process customer message and generate response."""
    conversation_history_str = format_conversation_history(state.get("conversation_history", []))
    
    prompt = GENERAL_SUPPORT_PROMPT.format(
        customer_context=state["customer_context"],
        customer_msg=state["customer_msg"],
        conversation_history=conversation_history_str
    )

    response = llm.invoke(prompt)
    
    # Update conversation history
    updated_history = state.get("conversation_history", []).copy()
    updated_history.append({"role": "customer", "content": state["customer_msg"]})
    updated_history.append({"role": "agent", "content": response.content})

    return {
        "agent_response": response.content,
        "conversation_history": updated_history,
        "status": "resolved"
    }