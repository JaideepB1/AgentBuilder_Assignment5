# AgentBuilder Assignment 5 - Sentinel

Sentinel is a multi-agent fraud triage system built with LangChain and LangGraph. It investigates alerted accounts using isolated specialist agents and produces a fraud disposition based on behavioral, contextual, and network evidence.

The system supports both single-account investigations and an asynchronous queue sweep of all 276 alerted accounts in the provided SQLite database.

## Architecture

The system uses four specialist agents coordinated by a supervisor:

- **Behaviour Specialist** - analyzes recent transactions against the account's historical behavior.
- **Context Specialist** - reads case notes, disputes, and prior fraud cases for customer-specific explanations.
- **Network Specialist** - checks shared devices and merchants for connections between accounts.
- **Disposition Specialist** - combines the specialist evidence and determines the final verdict and recommended action.

The supervisor does not have direct database access. It can only communicate with the specialists through specialist tools. Each specialist has its own message history and only receives tools relevant to its responsibility.

Fraud policies are stored as editable Markdown files in `policies/` and are loaded by specialists only when needed.

## Setup

The project uses Python and `uv`.

Install the dependencies:

```bash
uv sync
```

Create a `.env` file in the project root containing:

```text
OPENAI_API_KEY=your_key_here
```

The provided fraud dataset should be located at:

```text
data/sentinel.db
```

## Single Case

Pass an account ID to investigate one account:

```bash
uv run python main.py A00008
```

The system runs the specialist investigations, returns the final verdict and reasoning, and checks whether the recommended action requires human approval.

Recommended actions such as `escalate_case` and `block_card` trigger a human approval step before they can proceed:

```text
HUMAN APPROVAL REQUIRED:
Proposed action: escalate_case

Approve action? (yes/no):
```

Entering `yes` approves the proposed action. Entering `no` rejects it. Rejected actions are not automatically retried.

Actions such as `no_action` or `monitor` do not require approval.

## Queue Sweep

Run without an account ID to start the full queue sweep:

```bash
uv run python main.py
```

The queue manager creates a background job and returns a job ID immediately. The sweep then investigates all 276 alerted accounts.

The queue manager provides operations for:

- starting a sweep
- checking job status
- collecting completed results

The completed full sweep processed all 276 accounts with zero failed investigations.

## Output Files

- `DISPOSITIONS.md` - final verdict, confidence, and reasoning for all 276 accounts
- `CASES.md` - three detailed worked cases showing fraud, false-positive, and insufficient-evidence investigations
- `WRITEUP.md` - token measurements, single-agent comparison, and discussion of an evidence-transfer failure
- `sweep_results.json` - saved structured results from the completed queue sweep

## Verdicts

Every investigated account receives one of:

- `fraud`
- `legitimate`
- `insufficient_evidence`

Confidence is reported as:

- `high`
- `medium`
- `low`

The completed sweep produced:

- 166 legitimate
- 73 fraud
- 37 insufficient evidence

## Human Approval

Potentially irreversible actions are separated from the investigation itself using a LangGraph approval workflow with an `interrupt`.

The workflow pauses before:

- `block_card`
- `escalate_case`

It can then be resumed with either an approved or rejected decision. Both paths are preserved by the graph checkpointer.

## Policy Files

Editable policy documents are stored in:

```text
policies/
├── account_takeover.md
├── card_testing.md
├── escalation.md
└── travel.md
```

Specialists load these policies only when relevant instead of placing all policy information into every agent prompt.

## Project Structure

```text
AgentBuilder_Assignment5/
├── data/
│   └── sentinel.db
├── policies/
│   ├── account_takeover.md
│   ├── card_testing.md
│   ├── escalation.md
│   └── travel.md
├── agent.py
├── db.py
├── tools.py
├── policy_tools.py
├── queue_manager.py
├── main.py
├── generate_dispositions.py
├── DISPOSITIONS.md
├── CASES.md
├── WRITEUP.md
├── sweep_results.json
└── pyproject.toml
```

## Full Sweep Results

The completed 276-account sweep used **4,468,602 total model tokens**.

See `WRITEUP.md` for the token breakdown and discussion of the multi-agent context-isolation design.