from unittest.mock import patch, MagicMock
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
    mock_llm.invoke.return_value = mock_response

    state = {
        "messages": [],
        "scratchpad": "Planning...",
        "iteration": 0,
        "llm_calls": 0,
    }

    result = agent_node(state)

    assert "messages" in result
    assert result["iteration"] == 1
    assert result["llm_calls"] == 1
    mock_llm.invoke.assert_called_once()
