import threading

from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from dotenv import load_dotenv
from typing import Literal, TypedDict
from pydantic import BaseModel
from policy_tools import load_policy

from tools import (
    recent_transactions, 
    transaction_summary, 
    case_notes, 
    disputes, 
    prior_cases,
    shared_devices,
    shared_merchants,
    historical_transaction_summary,
)

load_dotenv()

model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)

class FraudVerdict(BaseModel):
    account_id: str
    verdict: Literal["fraud", "legitimate", "insufficient_evidence"]
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    recommended_action: Literal[
        "no_action",
        "monitor",
        "block_card",
        "escalate_case",
    ]

class InvestigationResult(BaseModel):
    account_id: str
    behaviour_summary: str
    context_summary: str
    network_summary: str
    verdict: Literal["fraud", "legitimate", "insufficient_evidence"]
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    recommended_action: Literal[
        "no_action",
        "monitor",
        "block_card",
        "escalate_case",
    ]

class ApprovalState(TypedDict):
    account_id: str
    verdict: str
    confidence: str
    reasoning: str
    recommended_action: str
    approval_status: str

def request_human_approval(account_id: str, action: str, reasoning: str):
    decision = interrupt(
        {
            "account_id": account_id,
            "proposed_action": action,
            "reasoning": reasoning,
            "message": f"Human approval required before {action}.",
        }
    )

    return decision

def check_approval(state: ApprovalState):
    action = state["recommended_action"]

    if action in ["block_card", "escalate_case"]:
        decision = request_human_approval(
            account_id=state["account_id"],
            action=action,
            reasoning=state["reasoning"],
        )

        return {
            "approval_status": decision
        }

    return {
        "approval_status": "not_required"
    }

def finalize_approval(state: ApprovalState):
    status = state["approval_status"]
    action = state["recommended_action"]

    if status == "approved":
        return {
            "approval_status": "approved"
        }

    if status == "rejected":
        return {
            "approval_status": "rejected"
        }

    return {
        "approval_status": "not_required"
    }


approval_builder = StateGraph(ApprovalState)

approval_builder.add_node("check_approval", check_approval)
approval_builder.add_node("finalize_approval", finalize_approval)

approval_builder.add_edge(START, "check_approval")
approval_builder.add_edge("check_approval", "finalize_approval")
approval_builder.add_edge("finalize_approval", END)

approval_checkpointer = InMemorySaver()

approval_graph = approval_builder.compile(
    checkpointer=approval_checkpointer
)

def investigate_account(account_id: str):
    result = supervisor_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Fully investigate account {account_id} "
                        "and determine its disposition."
                    ),
                }
            ]
        }
    )

    usage = get_token_usage(result["messages"])
    record_token_usage("supervisor", usage)

    investigation = result["structured_response"]

    return investigation

def investigate_single_case(account_id: str, thread_id: str):
    investigation = investigate_account(account_id)

    approval_result = approval_graph.invoke(
        {
            "account_id": investigation.account_id,
            "verdict": investigation.verdict,
            "confidence": investigation.confidence,
            "reasoning": investigation.reasoning,
            "recommended_action": investigation.recommended_action,
            "approval_status": "",
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    return {
        "investigation": investigation,
        "approval": approval_result,
    }

def resume_approval(thread_id: str, decision: str):
    if decision not in ["approved", "rejected"]:
        raise ValueError("Decision must be 'approved' or 'rejected'.")

    return approval_graph.invoke(
        Command(resume=decision),
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

BEHAVIOUR_PROMPT = """
You are a fraud investigation Behaviour specialist.

Your job is to determine whether an account's recent transaction behaviour
is normal or suspicious for that specific account.

Use your tools to examine:
- recent transactions
- the account's historical transaction baseline
- unusual transaction amounts
- rapid bursts of activity
- changes in channels, countries, merchants, or devices
- declined versus approved transactions

Do not make the final fraud verdict. Your responsibility is only to report
what the behavioural evidence shows.

Base every claim on evidence returned by your tools. Include relevant
transaction IDs, amounts, timestamps, devices, or other identifiers when
they support your conclusion.

Clearly state:
1. What you found
2. Why the behaviour is normal or abnormal
3. The strongest evidence supporting your assessment

Transaction analysis:
- Use recent_transactions to examine the activity currently being investigated.
- Use historical_transaction_summary as the older baseline for comparison.
- Compare recent amounts, devices, countries, channels, and authorization results against the historical baseline.
- Do not describe the recent suspicious transactions as part of the historical baseline.
- Cite specific transaction IDs when identifying important recent activity.

Policy guidance:
- You have access to a load_policy tool.
- After examining the transaction evidence, if you identify a pattern covered by an available policy, you MUST load the relevant policy before producing your final response.
- Load "account_takeover" when evidence involves unusual devices, unusual locations, account access, or sudden unexplained behavioural changes.
- Load "card_testing" when evidence involves rapid transaction attempts, repeated declines, or possible card-testing patterns.
- Load "travel" when geographic changes or foreign transactions are important to the investigation.
- Load only policies relevant to the evidence. Do not load every policy automatically.
- Apply relevant loaded policy guidance when explaining whether the behaviour is abnormal.
"""


behaviour_agent = create_agent(
    model=model,
    tools=[
    recent_transactions,
    historical_transaction_summary,
    load_policy,
    ],
    system_prompt=BEHAVIOUR_PROMPT,
)


CONTEXT_PROMPT = """
You are a fraud investigation Context specialist.

Your job is to determine whether customer-provided or historical context
helps explain suspicious activity on an account.

Use your tools to examine:
- case notes
- transaction disputes
- prior fraud cases

Pay close attention to the actual text written by customers or investigators.
A note or customer statement may explain activity that appears suspicious
from transaction data alone.

Do not make the final fraud verdict. Your responsibility is only to report
what the contextual evidence shows.

Base every claim on evidence returned by your tools. Include relevant
note IDs, dispute IDs, case IDs, dates, outcomes, and important details
from the text when they support your assessment.

Clearly state:
1. What contextual evidence you found
2. Whether it explains or increases concern about the flagged activity
3. The strongest evidence supporting your assessment

Policy guidance:
- You have access to a load_policy tool.
- First examine the customer's case notes, disputes, and prior cases.
- Load a policy only when the customer context makes that policy relevant.
- Load "account_takeover" when notes or disputes mention unexpected device registration, account access, password changes, or customer denial of activity.
- Load "travel" when notes or disputes mention travel, geographic activity, or authorized family members using the account abroad.
- Do not load policies that are unrelated to the evidence.
- Use the loaded policy to interpret the customer context, but do not make the final fraud disposition.
"""


context_agent = create_agent(
    model=model,
    tools=[case_notes, 
           disputes, 
           prior_cases, 
           load_policy,
    ],
    system_prompt=CONTEXT_PROMPT,
)

NETWORK_PROMPT = """
You are a fraud investigation Network specialist.

Your job is to determine whether an account appears to be acting alone
or whether its activity is connected to other accounts, devices, or
potentially risky merchants.

Use your tools to examine:
- devices shared with other accounts
- merchants used by the account
- merchant risk scores
- connections between the account and broader activity in the system

Do not make the final fraud verdict. Your responsibility is only to report
what the network evidence shows.

Do not assume that a shared device or commonly used merchant is fraudulent
by itself. Distinguish ordinary shared infrastructure from relationships
that provide meaningful evidence of coordinated or suspicious activity.

Merchant analysis:
- Shared merchants are weak network evidence when they are used by many accounts.
- Do not treat a high merchant risk score by itself as evidence that accounts are coordinated.
- Give more weight to unusually specific connections, especially shared devices.
- When discussing shared merchants, consider the account_count. A merchant used by hundreds of accounts is generally not evidence of a direct relationship between those accounts.

Base every claim on evidence returned by your tools. Include relevant
device IDs, merchant IDs, account counts, risk scores, or other identifiers
when they support your assessment.

Clearly state:
1. What network relationships you found
2. Whether those relationships appear suspicious or ordinary
3. The strongest evidence supporting your assessment
"""


network_agent = create_agent(
    model=model,
    tools=[shared_devices, shared_merchants],
    system_prompt=NETWORK_PROMPT,
)

DISPOSITION_PROMPT = """
You are a fraud investigation Disposition specialist.

Your job is to determine the appropriate final verdict after the Behaviour,
Context, and Network specialists have completed their investigations.

You do not investigate the database yourself. You make a decision only from
the evidence provided to you.

Choose exactly one verdict:
- fraud: the evidence strongly supports fraudulent activity
- legitimate: the evidence sufficiently supports legitimate customer activity
- insufficient_evidence: the available evidence does not support a defensible
  fraud or legitimate conclusion

Choose a confidence level of high, medium, or low.

Choose exactly one recommended action:
- no_action: no further fraud action is necessary
- monitor: keep the account under observation without taking an irreversible action
- block_card: recommend blocking the card because the evidence supports immediate fraud prevention
- escalate_case: recommend escalation for human investigation because the case requires further review

Use block_card or escalate_case only when justified by the evidence.
These actions require human approval and must not be treated as already executed.

Consider all evidence together. Do not treat a suspicious behavioural signal
as fraud automatically, and do not assume contextual evidence explains more
than it actually does.

If evidence is insufficient, clearly state what additional evidence would
help resolve the case.

Do not invent evidence.

Policy guidance:
- You have access to a load_policy tool.
- Before selecting the final recommended action, you MUST load the "escalation" policy.
- Apply the loaded policy when choosing between no_action, monitor, block_card, and escalate_case.
- Do not claim that block_card or escalate_case has been executed. These actions require human approval before execution.

After using any required tools, return only the final structured disposition.
Do not include commentary, explanations, markdown, or additional text outside the structured response.
"""


disposition_agent = create_agent(
    model=model,
    tools=[load_policy],
    system_prompt=DISPOSITION_PROMPT,
    response_format=ToolStrategy(FraudVerdict),
)

def get_token_usage(messages):
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    for message in messages:
        usage = getattr(message, "usage_metadata", None)

        if usage:
            input_tokens += usage.get("input_tokens", 0)
            output_tokens += usage.get("output_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }

token_usage_lock = threading.Lock()
token_usage_tracker = {
    "behaviour": 0,
    "context": 0,
    "network": 0,
    "disposition": 0,
    "supervisor": 0,
}

def record_token_usage(agent_name: str, usage: dict):
    with token_usage_lock:
        token_usage_tracker[agent_name] += usage["total_tokens"]

def get_total_token_usage():
    with token_usage_lock:
        return {
            **token_usage_tracker,
            "total": sum(token_usage_tracker.values()),
        }

def reset_token_usage():
    with token_usage_lock:
        for agent_name in token_usage_tracker:
            token_usage_tracker[agent_name] = 0

@tool
def investigate_behaviour(account_id: str) -> str:
    """Ask the Behaviour specialist to investigate an account's transaction behaviour."""

    result = behaviour_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Investigate the transaction behaviour for account {account_id}.",
                }
            ]
        }
    )

    usage = get_token_usage(result["messages"])
    record_token_usage("behaviour", usage)

    return result["messages"][-1].content

@tool
def investigate_context(account_id: str) -> str:
    """Ask the Context specialist to investigate an account's contextual evidence."""

    result = context_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Investigate the contextual evidence for account {account_id}.",
                }
            ]
        }
    )

    usage = get_token_usage(result["messages"])
    record_token_usage("context", usage)

    return result["messages"][-1].content

@tool
def investigate_network(account_id: str) -> str:
    """Ask the Network specialist to investigate an account's network evidence."""

    result = network_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Investigate the network evidence for account {account_id}.",
                }
            ]
        }
    )

    usage = get_token_usage(result["messages"])
    record_token_usage("network", usage)

    return result["messages"][-1].content

@tool
def determine_disposition(
    account_id: str,
    behaviour_evidence: str,
    context_evidence: str,
    network_evidence: str,
) -> dict:
    """Ask the Disposition specialist to determine the final verdict for an account."""

    result = disposition_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
Account: {account_id}

Behaviour evidence:
{behaviour_evidence}

Context evidence:
{context_evidence}

Network evidence:
{network_evidence}

Determine the disposition.
""",
                }
            ]
        }
    )

    verdict = result["structured_response"]

    usage = get_token_usage(result["messages"])
    record_token_usage("disposition", usage)

    return verdict.model_dump()


SUPERVISOR_PROMPT = """
You are the supervisor of a fraud investigation system.

Your job is to coordinate specialist agents to investigate an account.

You have specialist tools for:
- Behaviour: investigates whether transaction activity is normal or abnormal
- Context: investigates case notes, disputes, and prior fraud cases
- Network: investigates connections through devices and merchants

You do not have direct access to the database. You must use the specialists
to gather evidence.

For each account:
- Decide which investigative specialist to consult next based on the evidence
  gathered so far.
- Use the Behaviour, Context, and Network specialists when their evidence is
  relevant to understanding the case.
- You may choose the order in which investigative specialists are consulted
  and may request additional specialist analysis when needed.
- You MUST consult the Context specialist before asking the Disposition
  specialist for the final verdict.
- You MUST call the Disposition specialist before producing your final response.
The Disposition specialist is responsible for determining the final verdict
and recommended action. You must not determine the final disposition yourself.

Pay particular attention when contextual evidence explains activity that
appears suspicious from transaction data alone.

Do not invent evidence. Base your assessment only on evidence returned by
the specialists.

Preserve evidence identifiers in your summaries whenever they are available.
Important claims should remain traceable to their source evidence, including
transaction IDs, note IDs, dispute IDs, case IDs, device IDs, and merchant IDs.
Do not remove an identifier when it supports a key finding or final disposition.

For now, summarize:
- what Behaviour found
- what Context found
- what Network found
- how the evidence fits together

The Disposition specialist, not you, determines the final fraud verdict.
Return the Disposition specialist's verdict, confidence, and reasoning
along with a concise summary of the investigation.
"""


supervisor_agent = create_agent(
    model=model,
    tools=[
        investigate_behaviour,
        investigate_context,
        investigate_network,
        determine_disposition,
    ],
    system_prompt=SUPERVISOR_PROMPT,
    response_format=InvestigationResult,
)