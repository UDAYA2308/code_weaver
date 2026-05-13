from unittest.mock import patch, MagicMock
import asyncio

from src.code_weaver.graph import agent_node, should_continue


def test_should_continue_with_tools():
    # Mock state with a message that has tool_calls
    mock_msg = MagicMock()
    mock_msg.tool_calls = [{"name": "test_tool", "args": {}}]
    state = {"messages": [mock_msg]}

    assert should_continue(state) == "tools"


def test_should_continue_without_tools():
    # Mock state with a message that has no tool_calls
    mock_msg = MagicMock()
    # Use a property or mock to simulate missing tool_calls
    del mock_msg.tool_calls
    state = {"messages": [mock_msg]}

    from langgraph.graph import END

    assert should_continue(state) == END


@patch("src.code_weaver.graph.llm")
@patch("src.code_weaver.graph.load_system_prompt")
def test_agent_node(mock_load_prompt, mock_llm):
    mock_load_prompt.return_value = "System Prompt"

    # Mock the invoke method of the LLM
    mock_response = MagicMock()
    mock_response.content = "AI Response"
    
    # Use a Future to mock the async call
    future = asyncio.Future()
    future.set_result(mock_response)
    mock_llm.ainvoke.return_value = future

    state = {
        "messages": [],
    }

    # Mock config
    mock_config = {}

    result = asyncio.run(agent_node(state, mock_config))

    assert "messages" in result
    mock_llm.ainvoke.assert_called_once()
