from app.services.orchestrator import create_initial_state, run_customer_turn


def print_welcome():
    """Print welcome message."""
    print("\n" + "="*60)
    print("   🤖 CUSTOMER SUPPORT AI AGENT")
    print("="*60)
    print("\nWelcome to our AI-powered customer support system.")
    print("Type 'exit' or 'quit' to end the conversation.\n")


def get_customer_id():
    """Get customer ID from user input."""
    while True:
        try:
            customer_id_input = input("Enter your customer ID (or press Enter for demo): ").strip()
            if not customer_id_input:
                return 1  # Default demo customer
            customer_id = int(customer_id_input)
            if customer_id > 0:
                return customer_id
            else:
                print("❌ Please enter a positive number.")
        except ValueError:
            print("❌ Please enter a valid number.")


def should_exit(user_input):
    """Check if user wants to exit."""
    return user_input.lower() in ["exit", "quit", "bye"]


def run_conversation():
    """Run the conversational loop."""
    print_welcome()
    
    # Get customer ID
    customer_id = get_customer_id()
    print(f"✓ Connected with customer ID: {customer_id}\n")
    
    # Initialize state
    state = create_initial_state(customer_id)
    
    print("You: ", end="", flush=True)
    
    # Conversation loop
    while True:
        # Get user message
        user_message = input()
        
        # Check for exit
        if should_exit(user_message):
            print("\n👋 Thank you for using our support system. Goodbye!\n")
            break
        
        # Skip empty messages
        if not user_message.strip():
            print("You: ", end="", flush=True)
            continue
        
        # Update state with current message
        # Run graph
        print("\n🤖 Agent: ", end="", flush=True)
        try:
            result = run_customer_turn(state, user_message)
            
            # Print agent response
            print(result.get("agent_response", "(No response)"))
            
            # Update state with result
            state = result
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
        
        print("\nYou: ", end="", flush=True)


if __name__ == "__main__":
    run_conversation()