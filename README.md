# CS Agent - Customer Support AI Agent

A **conversational** multi-agent customer support system built with LangGraph and Groq AI.

## ✨ Key Features

- 🤖 **Fully Conversational** - Natural back-and-forth dialogue with conversation history
- 📝 **Context-Aware** - Agent maintains full conversation context across exchanges
- 👤 **Personalized** - Fetches and uses customer information for tailored responses
- 🔄 **Memory** - Complete conversation history is maintained and referenced
- 💡 **Intelligent** - Powered by Groq AI (with intelligent fallback mocking)
- 🚀 **Easy to Run** - Simple CLI interface, no setup required for demo mode

## Project Structure

```
CS-agent/
├── app/
│   ├── agents/
│   │   ├── escalation.py
│   │   ├── supervisor.py
│   │   └── specialists/
│   │       ├── account.py
│   │       ├── billing.py
│   │       ├── feature.py
│   │       ├── general.py
│   │       └── technical.py
│   ├── graph/
│   │   ├── builder.py          # LangGraph workflow builder
│   │   ├── load_customer.py    # Customer data loading
│   │   └── state.py            # State management
│   ├── services/
│   │   ├── database.py         # PostgreSQL database connection
│   │   └── llm.py              # Groq LLM service
│   ├── tools/
│   │   └── customer_lookup.py  # Customer lookup utilities
│   ├── prompts/
│   │   ├── general.py
│   │   ├── account.py
│   │   ├── billing.py
│   │   ├── feature_request.py
│   │   └── technical.py
│   ├── scripts/
│   │   └── seed_db.py          # Database seeding script
│   ├── memory/                 # Memory storage (future)
│   └── main.py                 # Main application entry point
├── run.py                      # Project root entry point
├── requirements.txt            # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.8+
- PostgreSQL database running locally
- Groq API key

## Setup Instructions

### 1. Create a Python Virtual Environment

```bash
cd /home/halley/Desktop/projects/CS-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Set Up PostgreSQL Database

Create the customer support database and tables:

```sql
CREATE DATABASE customer_support;

-- Connect to the database
\c customer_support;

-- Create customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    subscription_plan VARCHAR(50) NOT NULL,
    account_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    order_status VARCHAR(50) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Seed the Database (Optional)

If you want to populate the database with sample data:

```bash
# First, update database credentials in app/scripts/seed_db.py if needed
python3 app/scripts/seed_db.py
```

**Note:** Update the database credentials in `app/scripts/seed_db.py` to match your PostgreSQL setup.

### 6. Update Database Credentials

Update the database connection credentials in:
- `app/services/database.py`
- `app/scripts/seed_db.py`

Change the connection parameters:
```python
psycopg2.connect(
    host="localhost",      # Your PostgreSQL host
    port=5432,             # Your PostgreSQL port
    user="postgres",       # Your PostgreSQL user
    password="postgres",   # Your PostgreSQL password
    dbname="customer_support"
)
```

## Running the Application

### Quick Start (Recommended)

```bash
cd /home/halley/Desktop/projects/CS-agent
python3 run.py
```

Then:
1. Press Enter for demo customer (ID 1) or enter your own customer ID
2. Type your questions naturally
3. Type `exit` or `quit` to end the conversation

### Example Conversation

```
Enter your customer ID (or press Enter for demo): [Press Enter]
✓ Connected with customer ID: 1

You: What's my subscription plan?
🤖 Agent: Hello! You're currently on our Enterprise plan with an Active account status...

You: Can I upgrade?
🤖 Agent: Based on your current Enterprise plan, I can discuss upgrade options with you...

You: exit
👋 Thank you for using our support system. Goodbye!
```

### From App Directory

```bash
cd /home/halley/Desktop/projects/CS-agent/app
python3 main.py
```

## Conversational Features

### Dynamic Conversation Flow
- **Multi-turn dialogue** - Ask follow-up questions naturally
- **Full context** - Agent remembers everything from the conversation
- **Customer info** - System loads and uses your customer data
- **Smart responses** - AI understands context and provides relevant help

### Conversation History
Every exchange is tracked:
- Customer messages
- Agent responses  
- Complete context including customer details, orders, and previous interactions

### Exit Options
- Type `exit` - ends conversation
- Type `quit` - ends conversation
- Type `bye` - ends conversation

## Understanding the Flow

1. **Welcome** → System greets you and asks for customer ID
2. **Customer Load** → Your information is fetched from the database (or uses demo data)
3. **Conversation Loop** → 
   - You type a message
   - Agent processes message with full conversation context
   - Agent responds with relevant information
   - Conversation history is updated
   - Ready for next message
4. **Exit** → Type 'exit' to end

For detailed usage information, see [USAGE_GUIDE.md](USAGE_GUIDE.md).

## Key Fixes Applied

The following issues were identified and fixed:

1. ✅ **Filename Typo**: Fixed `curtomer_lookup.py` → `customer_lookup.py`
2. ✅ **Missing Package Init Files**: Created `__init__.py` files in all directories
3. ✅ **Import Path Errors**: Fixed import statements to reference correct modules
   - Fixed `from agents.general_support` → `from agents.specialists.general`
   - Fixed `from prompts.general_support` → `from prompts.general`
4. ✅ **LLM Export**: Changed `groq_model` export to `llm` in `services/llm.py`
5. ✅ **Python Path Setup**: Updated `main.py` with proper sys.path handling
6. ✅ **Entry Point**: Created `run.py` for easy execution from project root
7. ✅ **State Field Typo**: Fixed `convesation_history` → `conversation_history`
8. ✅ **Dependencies**: Added `psycopg2-binary` and `faker` to `requirements.txt`

## Architecture

The application uses LangGraph to build a multi-agent workflow:

1. **Graph Builder** (`graph/builder.py`): Defines the workflow pipeline
2. **State Management** (`graph/state.py`): Defines the conversation state
3. **Customer Loading** (`graph/load_customer.py`): Fetches customer context
4. **LLM Integration** (`services/llm.py`): Groq AI model integration
5. **Database Service** (`services/database.py`): PostgreSQL connection
6. **Specialist Agents** (`agents/specialists/`): Domain-specific agents
7. **Prompts** (`prompts/`): Agent-specific prompts and instructions

## Development

### Running in Development Mode

For development with auto-reload, you can use tools like `watchmedo`:

```bash
pip install watchdog[watchmedo]
watchmedo auto-restart -d app -p '*.py' -- python3 run.py
```

### Debugging

Enable debug logging by setting environment variables:

```bash
export DEBUG=1
python3 run.py
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running on localhost:5432
- Check credentials in `app/services/database.py`
- Verify the `customer_support` database exists

### Groq API Key Error
- Ensure `.env` file exists with `GROQ_API_KEY` set
- Verify the API key is valid

### Import Errors
- Ensure you're running from the project root or using `run.py`
- Verify virtual environment is activated
- All `__init__.py` files should be present in package directories

## License

[Add your license here]
