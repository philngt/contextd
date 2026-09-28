def can_cancel(state):
    return state in {"NEW", "PAID"}
