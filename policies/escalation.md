# Disposition and Escalation Policy

## Legitimate

Use `legitimate` when the available evidence provides a convincing explanation for the flagged activity and there is no strong contradictory fraud evidence.

Possible actions:

- `no_action` when the activity is sufficiently explained.
- `monitor` when the activity appears legitimate but some uncertainty remains.

## Fraud

Use `fraud` when the available evidence strongly supports unauthorized or fraudulent activity.

Possible actions:

- `block_card` when continued card activity creates an immediate fraud risk.
- `escalate_case` when the case requires further fraud investigation or operational review.

## Insufficient Evidence

Use `insufficient_evidence` when the available evidence does not support a defensible fraud or legitimate determination.

The reasoning must identify what additional evidence would help resolve the case.

Possible actions:

- `monitor`
- `escalate_case` when additional investigation is necessary.

## Human Approval

The following actions are irreversible or operationally significant and require human approval before execution:

- `block_card`
- `escalate_case`

A rejected action must not be executed or automatically retried.