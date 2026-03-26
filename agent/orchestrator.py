"""
Week 2 — Agent Orchestrator
Manages the Claude API interaction loop:
  user question → tool calls → tool results → synthesised answer
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOOL_ITERATIONS
from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    TOOL_DEFINITIONS,
    get_fleet_summary,
    get_vehicle_profile,
    get_branch_health,
    get_fuel_forecast,
    find_high_risk_vehicles,
    find_cross_model_alerts,
)

TOOL_MAP = {
    "get_fleet_summary": get_fleet_summary,
    "get_vehicle_profile": get_vehicle_profile,
    "get_branch_health": get_branch_health,
    "get_fuel_forecast": get_fuel_forecast,
    "find_high_risk_vehicles": find_high_risk_vehicles,
    "find_cross_model_alerts": find_cross_model_alerts,
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _call_tool(name: str, inputs: dict) -> str:
    """Execute a tool and return its result as a JSON string."""
    fn = TOOL_MAP.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**inputs)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def ask(question: str, verbose: bool = False) -> str:
    """
    Send a question to the agent and return its final answer.
    Runs the tool-calling loop until Claude produces a text response.
    """
    messages = [{"role": "user", "content": question}]

    for iteration in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if verbose:
            print(f"\n[Agent iteration {iteration + 1}] stop_reason={response.stop_reason}")

        # If Claude is done, return its text
        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_blocks)

        # Process tool calls
        if response.stop_reason == "tool_use":
            # Add Claude's response (which contains tool_use blocks) to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"  → Calling tool: {block.name}({block.input})")
                    result = _call_tool(block.name, block.input)
                    if verbose:
                        preview = result[:200] + "..." if len(result) > 200 else result
                        print(f"  ← Result: {preview}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Add tool results to messages and loop
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — return whatever text we have
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_blocks) if text_blocks else f"[Stopped: {response.stop_reason}]"

    return "[Max iterations reached]"
