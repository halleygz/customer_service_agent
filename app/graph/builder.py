from langgraph.graph import (
    StateGraph,
    START,
    END
)

from graph.state import CustomerState

from graph.load_customer import (
    load_customer_context
)

from agents.specialists.general import (
    general_support_agent
)

builder = StateGraph(CustomerState)

builder.add_node(
    "load_customer_context",
    load_customer_context
)

builder.add_node(
    "general_support_agent",
    general_support_agent
)

builder.add_edge(
    START,
    "load_customer_context"
)

builder.add_edge(
    "load_customer_context",
    "general_support_agent"
)

builder.add_edge(
    "general_support_agent",
    END
)

graph = builder.compile()