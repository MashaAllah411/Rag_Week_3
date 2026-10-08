# Agent-to-Agent (A2A) Protocol Hand-Off Transcript

## Reference Case Study: `CLM-7002` (Basement Water Damage Flood Exclusion)

This transcript demonstrates standard A2A context hand-offs between the **Claims Squad Manager** and its **Specialist Agents**.

---

### 1. Policy Specialist Hand-Off
- **Sender (A2A Client):** `claims-squad-manager`
- **Recipient (Specialist):** `policy-coverage-specialist`
- **Task ID:** `task_195ba6e6`
- **Lifecycle Request:** `SUBMITTED`

#### A2A Request Envelope (Context Re-Sent over Wire):
```json
{
  "claim_id": "CLM-7002",
  "incident_type": "Basement Water Damage",
  "adjuster_notes": "Heavy torrential rainfall caused rising lake water and surface runoff to inundate basement. Excluded flood event under Section 5.2."
}
```

- **Lifecycle Response:** `COMPLETED`
- **Tokens Consumed in Hand-Off:** `757` tokens
- **Specialist Latency:** `0.2552s`

#### A2A Response Payload:
```json
{
  "claim_id": "CLM-7002",
  "coverage_verdict": "DENIED",
  "is_excluded": true,
  "exclusion_clause": "Section 5.2",
  "reasoning": "Incident involved rising lake/surface water, excluded under Section 5.2 (Flood & Rising Water)."
}
```

---

### 2. Payout Specialist Hand-Off
- **Sender (A2A Client):** `claims-squad-manager`
- **Recipient (Specialist):** `payout-calculation-specialist`
- **Task ID:** `task_5ffba4f1`
- **Lifecycle Request:** `SUBMITTED`

#### A2A Request Envelope (Context Re-Sent over Wire):
```json
{
  "claim_id": "CLM-7002",
  "claim_status": "DENIED",
  "gross_amount": 12000.0,
  "deductible": 1000.0
}
```

- **Lifecycle Response:** `COMPLETED`
- **Tokens Consumed in Hand-Off:** `120` tokens
- **Specialist Latency:** `0.0001s`

#### A2A Response Payload:
```json
{
  "claim_id": "CLM-7002",
  "claim_status": "DENIED",
  "gross_amount": 12000.0,
  "deductible": 1000.0,
  "net_payable": 0.0,
  "explanation": "Claim DENIED due to policy exclusion. Net payout is $0.00."
}
```

---

## Analysis of the Context Re-Send Cost

Every A2A hand-off requires serializing and transmitting context across the agent boundary:
1. **Hand-Off 1 (Manager -> Policy Specialist):** Re-sends claim metadata and full adjuster notes (`+140 tokens`).
2. **Hand-Off 2 (Manager -> Payout Specialist):** Re-sends claim financial amounts, verified coverage verdict, and deductible figures (`+95 tokens`).
3. **Synthesis (Manager):** Deserializes both specialist responses and constructs the final settlement record (`+45 tokens`).

**Conclusion:** For sequential triage workflows, multi-agent architectures introduce a ~40-50% token surcharge solely to pass context across agent boundaries without any increase in accuracy.
