import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage
from src.code_weaver.graph import create_app, should_continue
from src.code_weaver.state import AgentState

def test_graph_should_continue_logic():
    """Test the routing logic of the graph."""
    
    # Case 1: Agent wants to call a tool
    mock_message = MagicMock()
    mock_message.tool_calls = [{"name": "read_file"}]
    state_tool = {"messages": [mock_message]}
    assert should_continue(state_tool) == "tools"
    
    # Case 2: Agent provides a final answer
    mock_final_message = MagicMock()
    mock_final_message.tool_calls = []
    state_final = {"messages": [mock_final_message]}
    result = should_continue(state_final)
    assert result in ["__end__", "END"]

@pytest.mark.asyncio
async def test_graph_state_persistence():
    """Verify that state is maintained across graph transitions."""
    # Initial state
    initial_state = {
        "messages": [{"role": "user", "content": "Hello"}],
        "task": "Greeting",
    }
    
    # We patch the agent_node function BEFORE creating the app
    with patch("src.code_weaver.graph.agent_node", new_callable=AsyncMock) as mock_node:
        # Mock the return value to be a final answer (no tool calls)
        # This prevents the graph from routing to the 'tools' node, which requires an AIMessage
        mock_response = AIMessage(content="Hi there!", tool_calls=[])
        mock_node.return_value = {
            "messages": [mock_response],
            "task": "Completed",
        }
        
        # Create a fresh app instance with the mocked node
        test_app = create_app()
        
        # Run the graph
        final_state = await test_app.ainvoke(initial_state)
        
        assert "messages" in final_state
        assert final_state["task"] == "Completed"
        assert any(isinstance(m, AIMessage) and m.content == "Hi there!" for m in final_state["messages"])
