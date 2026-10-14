from pathlib import Path
from langchain_core.tools import tool

POLICY_DIR = Path("policies")

@tool
def load_policy(policy_name: str) -> str:
    """Load a fraud policy document when it is relevant to the current investigation."""

    allowed_policies = {
        "account_takeover",
        "card_testing",
        "travel",
        "escalation",
    }

    if policy_name not in allowed_policies:
        return f"Unknown policy: {policy_name}"

    policy_path = POLICY_DIR / f"{policy_name}.md"

    return policy_path.read_text()