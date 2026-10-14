from langchain_core.tools import tool

from db import (
    get_recent_transactions,
    get_transaction_summary,
    get_case_notes,
    get_disputes,
    get_prior_cases,
    get_shared_devices,
    get_shared_merchants,
    get_historical_transaction_summary,
)


@tool
def recent_transactions(account_id: str, limit: int = 20) -> list[dict]:
    """Get the most recent transactions for an account.

    Use this to inspect the account's recent spending behaviour,
    including transaction amounts, channels, countries, merchants,
    devices, and authorization results.
    """
    return get_recent_transactions(account_id, limit)

@tool
def transaction_summary(account_id: str) -> dict:
    """Get a historical transaction summary for an account.

    Use this to establish the account's normal spending baseline,
    including transaction count, average amount, minimum and maximum
    amounts, and number of declined transactions.
    """
    return get_transaction_summary(account_id)

@tool
def case_notes(account_id: str) -> list[dict]:
    """Get case notes associated with an account's customer.

    Use this to check whether the customer previously provided context
    that may explain activity on the account.
    """
    return get_case_notes(account_id)

@tool
def disputes(account_id: str) -> list[dict]:
    """Get disputes associated with transactions on an account.

    Use this to check whether the customer disputed transactions
    and what the customer said about them.
    """
    return get_disputes(account_id)


@tool
def prior_cases(account_id: str) -> list[dict]:
    """Get prior fraud cases associated with an account's customer.

    Use this to inspect previous investigations, their outcomes,
    and the evidence summarized in those cases.
    """
    return get_prior_cases(account_id)

@tool
def shared_devices(account_id: str) -> list[dict]:
    """Find devices used by this account that are also used by other accounts.

    Use this to identify shared-device relationships between accounts
    that may indicate coordinated activity or a broader network.
    """
    return get_shared_devices(account_id)

@tool
def shared_merchants(account_id: str, limit: int = 10) -> list:
    """Find the highest-risk merchants used by this account that are also used by other accounts."""
    return get_shared_merchants(account_id, limit)

@tool
def historical_transaction_summary(
    account_id: str,
    exclude_recent: int = 20,
) -> dict:
    """Summarize an account's older transaction history, excluding its most recent transactions, to provide a historical baseline."""
    return get_historical_transaction_summary(
        account_id,
        exclude_recent,
    )