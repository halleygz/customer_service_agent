from app.prompts.technical import TECHNICAL_SUPPORT_PROMPT
from app.services import llm
from app.utils.format_history import format_conversation_history


def feature_request_agent(state):
    conv_history = format_conversation_history(state.get("conversation_history", []))

    prompt = TECHNICAL_SUPPORT_PROMPT.format(
        customer_context = state["customer_context"],
        customer_msg = state["customer_msg"],
        conversation_history=conv_history
    )

    response = llm.invoke(prompt)

    # if there is a bug that is caught use the bug report tool to report the bug
    
    updated_history = state.get("conversation_history", []).copy()
    updated_history.append({"role": "customer", "content": state["customer_msg"]})
    updated_history.append({"role": "agent", "content": response.content})

    return {
        "agent_response": response.content,
        "conversation_history": updated_history,
        "status": "resolved"
    }
