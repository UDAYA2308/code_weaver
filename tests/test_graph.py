from unittest.mock import patch, MagicMock
import asyncio

from code_weaver.graph import agent_node, should_continue


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
