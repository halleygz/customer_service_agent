from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()


class MockLLM:
    """Mock LLM for testing without or with unavailable Groq API key."""
    def invoke(self, prompt: str):
        """Return a mock response."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        return MockMessage(
            f"[Mock AI Response] Thank you for your inquiry. I've reviewed your customer information and message. "
            f"Based on the context provided, I'm processing your request about subscription details. "
            f"For production use, please configure a valid GROQ_API_KEY environment variable with an active Groq account."
        )


class RobustLLM:
    """Wrapper around ChatGroq that falls back to mock on API errors."""
    def __init__(self, groq_model):
        self.groq_model = groq_model
        self.mock_model = MockLLM()
    
    def invoke(self, prompt: str):
        """Try to invoke Groq model, fall back to mock on error."""
        try:
            return self.groq_model.invoke(prompt)
        except Exception as e:
            print(f"⚠️  API Error: {type(e).__name__}: {str(e)[:100]}... Using mock response instead.")
            return self.mock_model.invoke(prompt)


# Initialize Groq AI model using LangChain
def get_groq_model(model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
    """
    Initialize and return a Groq AI model instance using LangChain.
    
    Args:
        model_name: The Groq model to use (default: llama-3.3-70b-versatile)
        temperature: Temperature for model sampling (default: 0.7)
    
    Returns:
        RobustLLM or MockLLM: Configured model instance wrapped with fallback or mock
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("⚠️  Warning: GROQ_API_KEY environment variable not set. Using mock LLM for testing.")
        return MockLLM()
    
    try:
        groq_model = ChatGroq(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        # Wrap with robust error handling
        return RobustLLM(groq_model)
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Groq model ({e}). Using mock LLM instead.")
        return MockLLM()


# Default model instance
llm = get_groq_model()
