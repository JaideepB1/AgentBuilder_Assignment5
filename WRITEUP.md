# Sentinel Write-Up

## Token Usage

The full queue sweep processed all 276 alerted accounts successfully with no failed investigations.

Measured token usage by component:

| Component | Tokens |
|---|---:|
| Behaviour specialist | 1,620,662 |
| Context specialist | 437,648 |
| Network specialist | 485,267 |
| Disposition specialist | 502,845 |
| Supervisor | 1,422,180 |
| **Total** | **4,468,602** |

This is approximately 16,191 tokens per account. Token usage was recorded from the model usage metadata during the sweep and accumulated separately for each specialist and the supervisor.

## Single-Agent Estimate

A single-agent implementation was not run across all 276 accounts, so its token usage is estimated rather than measured.

To estimate the additional context a single agent would need to carry, I measured the evidence retrieved from the database for all 276 accounts. The average evidence size per account was approximately:

- Behaviour evidence: 3,883 characters
- Context evidence: 369 characters
- Network evidence: 1,491 characters
- Combined evidence: approximately 5,744 characters

In the multi-agent implementation, each specialist receives only the tools and context needed for its responsibility and returns a final summary to the supervisor. A comparable single agent would instead accumulate the Behaviour, Context, and Network evidence in the same message history. As the investigation progresses, earlier tool results would remain in context and be sent again on later model calls.

Using the common approximation of about four characters per token, the raw evidence is roughly 1,436 tokens per account. If the single agent performs four major reasoning stages while accumulating this evidence, repeated evidence alone would add several thousand input tokens per account beyond a fully isolated design. Across 276 accounts, this represents roughly one million additional input tokens from repeated raw evidence alone.

This is a conservative estimate because it does not include additional repetition of prompts, reasoning messages, tool-call messages, or other conversation history. Therefore, I would expect a comparable single-agent implementation to consume more than the measured **4,468,602 tokens** used by the specialist architecture, but I would not claim an exact token count without actually running that implementation.

## Most Difficult Case

The case I believe the system handled most poorly was **A00184**. The system classified it as legitimate with medium confidence, but manual review revealed an evidence-linking problem between the Context specialist and the supervisor.

The Behaviour specialist identified five unusual transactions (T0107937–T0107941), each for 50,000, compared with a historical maximum of 7,800. The Context specialist found case note N00240 explaining that the customer runs a trading business with lumpy transaction volumes. It also found open dispute DP0084 and summarized it as evidence of customer awareness.

The important detail was that DP0084 actually refers to transaction **T0016928**, not any of the five suspicious transactions identified by the Behaviour specialist. That relationship was not preserved clearly enough in the Context specialist's summary. As a result, the supervisor reasoned that "the customer is aware of the high-value transaction as indicated by the open dispute," incorrectly connecting evidence from two different transactions.

This exposed a weakness of returning only specialist summaries. The supervisor correctly did not receive the Context agent's full tool history, but that means important identifiers must survive summarization. In this case, losing the connection between DP0084 and T0016928 allowed the supervisor to use the dispute as support for the wrong transactions.

I would improve the system by requiring the Context specialist to preserve transaction IDs whenever it reports disputes and explicitly state whether each dispute is connected to one of the transactions identified by the Behaviour specialist.