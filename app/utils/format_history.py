def format_conversation_history(history):
    """Format conversation history for the prompt."""
    if not history:
        return "[No previous messages]"
    
    formatted = []
    for msg in history:
        role = msg.get("role", "Unknown").upper()
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)