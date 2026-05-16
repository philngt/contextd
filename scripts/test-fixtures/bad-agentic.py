"""Fixture: triggers pack-agentic rules."""

from typing import Any


def tool(fn):
    return fn


@tool
def delete_user(user_id: str) -> dict:  # destructive, no `confirm` param
    """Delete a user permanently."""
    # no timeout
    db.execute(f"DELETE FROM users WHERE id = {user_id}")
    return {"deleted": user_id}


@tool
def fetch_data(query: str) -> dict:
    # no timeout wrapper
    return external_api.get(query)


def agent_loop(task: str):
    """Plan + execute steps."""
    history = []
    while True:  # unbounded — no max steps, no break
        action = plan_next(task, history)
        result = execute_tool(action)
        history.append((action, result))


def bounded_agent(task: str):
    MAX_STEPS = 50
    for step in range(MAX_STEPS):
        action = plan_next(task)
        # no trace / log of step
        result = execute_tool(action)
        if action.is_terminal():
            break
