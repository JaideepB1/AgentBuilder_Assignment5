# Worked Cases

## Obvious Fraud — A00008

### Behaviour Specialist
The Behaviour specialist found abnormal high-value transactions across multiple new countries (DE, GB, and AE) using a new device, DX01439. This contrasted with the account's historical activity, which was mostly in India using device D000080. It also identified rapid geographic changes and a declined high-value transaction. Important transactions included T0107081, T0107082, and T0107083.

### Context Specialist
The Context specialist found case note N00051. The customer reported an unexpected device registration and denied traveling or losing possession of the card. There were no prior disputes or fraud cases. This provided textual evidence supporting the possibility of account takeover rather than explaining the unusual transactions as legitimate.

### Network Specialist
The Network specialist found no devices shared with other accounts, so there was no evidence of direct device-based coordination. Although some shared merchants had high risk scores, those merchants were used by many accounts. The specialist therefore did not treat those merchants as evidence of a coordinated fraud network.

### Supervisor and Disposition
The transaction pattern and customer context both supported account takeover. The lack of network connections did not contradict that conclusion because an account takeover does not require coordination with other customer accounts. The final disposition was **fraud** with **high confidence**.

**Recommended action:** `escalate_case`

The escalation is an irreversible action in the workflow and therefore requires human approval before execution.

## Convincing False Positive — A00000

### Behaviour Specialist
The Behaviour specialist found a sudden increase in transaction amounts in transactions T0107392 through T0107395, ranging from approximately 10,262 to 20,978. These transactions occurred through the app from Singapore using a new device, DX01459. Historical activity was much smaller and primarily occurred in India and Thailand using device D000000. Based on transaction behavior alone, the activity appeared abnormal and potentially consistent with account takeover.

### Context Specialist
The Context specialist found case note N00106, which explains that the second device belongs to the customer's son in Singapore and that he legitimately uses the card. There were no disputes or recent fraud cases raising additional concerns. Prior case PC0025 was also determined to be a false positive involving confirmed legitimate transactions. This context provided a direct explanation for the otherwise suspicious behavior.

### Network Specialist
The Network specialist found no devices shared with other accounts. The shared merchants were common merchants used by many accounts and had moderate to low risk scores. Therefore, there was no strong network evidence suggesting coordinated fraud.

### Supervisor and Disposition
Although the Behaviour specialist identified a pattern that initially appeared suspicious, the Context specialist found customer-specific evidence explaining both the new device and the Singapore activity. The Network specialist also found no suspicious account connections. The contextual evidence therefore outweighed the behavioral anomaly, and the final disposition was **legitimate** with **high confidence**.

**Recommended action:** `no_action`

## Insufficient Evidence — A00031

### Behaviour Specialist
The Behaviour specialist found a very large transaction, T0107693, for 84,170.08 INR, far exceeding the account's historical maximum of 2,915.50 INR. Recent activity also showed rapid geographic changes across India, the Netherlands, Thailand, and Singapore. Although the device remained consistent, the unusually large amount and geographic spread made the activity abnormal.

### Context Specialist
The Context specialist found conflicting evidence. Case note N00182 states that the customer planned a high-value jewelry purchase of approximately 84,170 INR and had been warned that the purchase could trigger fraud alerts. However, dispute DP0068 was opened for transaction T0107693. The customer recognized the merchant but stated that the transaction amount was higher than expected. There were no prior fraud cases.

### Network Specialist
The Network specialist found no devices shared with other accounts. Although some merchants were high risk, they were also widely used by other accounts, so this was not treated as strong evidence of coordinated fraud. The network evidence therefore did not resolve the conflicting Behaviour and Context evidence.

### Supervisor and Disposition
The Behaviour specialist found significant anomalies, but the Context specialist found evidence that both explained and questioned the transaction. The planned jewelry purchase explains why a transaction near 84,170 INR could be legitimate, while the customer's dispute over the exact amount prevents the transaction from being confidently accepted as authorized. Network evidence did not resolve this conflict.

The final disposition was **insufficient_evidence** with **medium confidence**.

Additional evidence that could resolve the case includes transaction authorization details, confirmation from the customer about the exact authorized amount, and verification from the merchant.

**Recommended action:** `escalate_case`

Because escalation is an irreversible action in the workflow, it requires human approval before execution.