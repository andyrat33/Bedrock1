# AWS Bedrock Guardrails — Setup Guide

## Overview
Guardrails sit in front of the agent and filter both incoming user messages and outgoing
agent responses. They are versioned independently from agents — attach a guardrail version
to an agent, then re-Prepare and re-version the agent to deploy changes.

**Guardrail name:** `test-guard`  
**Use case:** T-shirt store customer support agent

---

## Part 1 — Create the Guardrail

**Amazon Bedrock → Guardrails → Create guardrail**

### Guardrail details

| Field | Value |
|---|---|
| Name | `test-guard` |
| Description | T-shirt store content policy |

### Blocked messaging

| Field | Value |
|---|---|
| Blocked input message | `I am not allowed to answer this question per my company's policy.` |
| Blocked output message | `I am not allowed to answer this question per my company's policy.` |

> Set both fields identically. **Input** fires when the user's message is blocked;
> **output** fires when the agent's response is blocked.

Click **Next**.

---

## Part 2 — Content Filters

Content filters score each message across harmful categories and block anything above
your threshold. Applied to both user input and agent output.

| Category | Input strength | Output strength |
|---|---|---|
| Hate | High | High |
| Insults | High | High |
| Sexual | High | High |
| Violence | Medium | Medium |
| Misconduct | Medium | Medium |
| Prompt attack | High | N/A *(input only)* |

> **Tuning:** Start High for Hate/Insults. If legitimate messages get blocked, drop to
> Medium. Prompt attack only applies to input — it catches jailbreak attempts.

Click **Next**.

---

## Part 3 — Denied Topics

Denied topics use an LLM to detect whether a message matches a plain-English description —
more flexible than keyword matching, context-aware.

### Topic 1 — Competitors

| Field | Value |
|---|---|
| Name | `Competitors` |
| Type | Deny |
| Definition | `Any discussion, comparison, or recommendation of competing retail stores or brands, including but not limited to Walmart, Target, Gap, H&M, Zara, Amazon, or any other clothing or general merchandise retailer.` |
| Sample phrases | `"Is Target cheaper?"` · `"Does Gap have this in stock?"` · `"How do you compare to Walmart?"` |

### Topic 2 — Internal Customer IDs

| Field | Value |
|---|---|
| Name | `Internal Customer IDs` |
| Type | Deny |
| Definition | `Any request to reveal, look up, or discuss internal customer identifiers, account numbers, or database IDs used by the company's internal systems. These are not for customer-facing use.` |
| Sample phrases | `"What is my internal customer ID?"` · `"Can you tell me the account reference for order 123?"` |

> **Writing good definitions:** Be specific and include named examples. The more precise
> the definition, the fewer false positives and false negatives.

Click **Next**.

---

## Part 4 — Word Filters

Exact keyword matching (case-insensitive). Use for terms that are *always* unacceptable
regardless of context. For context-sensitive blocking, use Denied Topics instead.

**Enable profanity filter:** Yes (AWS managed list)

**Custom word blocklist:**

| Word |
|---|
| `cryptocurrency` |
| `bitcoin` |
| `crypto` |
| *(add political names one per line as needed)* |

> **Warning:** Word filters are blunt — `bitcoin` blocks the word everywhere, including
> `"We don't accept bitcoin"`. Only use for terms with zero legitimate use in your context.

Click **Next**.

---

## Part 5 — Sensitive Information (PII & Regex)

Optional. Blocks or redacts personally identifiable information.

### Built-in PII detectors

Select any type and choose **Block** or **Anonymize**:

| PII type | Example |
|---|---|
| `US_SOCIAL_SECURITY_NUMBER` | `123-45-6789` |
| `EMAIL` | `user@example.com` |
| `PHONE` | `+1-555-123-4567` |
| `CREDIT_DEBIT_CARD_NUMBER` | `4111 1111 1111 1111` |

### Custom regex patterns

For proprietary internal formats:

| Field | Value |
|---|---|
| Name | `Internal Customer ID` |
| Pattern | `CUST-\d{6}` *(matches `CUST-123456`)* |
| Action | Block |

> **Block** returns the blocked message. **Anonymize** replaces the matched value with a
> placeholder like `[CUSTOMER_ID]` — useful for keeping logs readable while protecting data.

Click **Next → Review → Create guardrail**.

---

## Part 6 — Test Before Attaching

**Guardrails → test-guard → Test**

| Input | Expected result |
|---|---|
| `"Is Target cheaper than you?"` | Blocked — Competitors topic |
| `"What is my internal customer ID?"` | Blocked — Internal Customer IDs topic |
| `"Do you accept cryptocurrency?"` | Blocked — word filter |
| `"I hate your t-shirts"` | Blocked — Hate content filter |
| `"What colour is this shirt?"` | Allowed |

---

## Part 7 — Attach to the Agent

### 7.1 Open the agent

**Bedrock → Agents → Customer Support Agent → Edit (Working draft)**

### 7.2 Add the guardrail

Scroll to **Guardrails** → **Select guardrail**:

| Field | Value |
|---|---|
| Guardrail | `test-guard` |
| Version | `1` |

Click **Save**.

### 7.3 Prepare the agent

**Agent overview → Prepare** — wait for status: **Prepared**

### 7.4 Create a new Version

**Agent overview → Create version**

| Field | Value |
|---|---|
| Description | `v2 - added test-guard guardrail` |

### 7.5 Update the Alias

**Aliases → prod → Edit** → Route 100% to **Version 2**

> To roll back: point the alias back to Version 1 — instant, no code changes.

---

## Guardrail Versioning

Guardrails version independently from agents. When you update the guardrail:

```
Edit guardrail → Create new guardrail version →
Update agent to reference new version → Prepare agent →
Create new agent version → Update alias
```

---

## Guardrail Test Results

Tested against `prod` alias (agent version 2) on 2026-05-12:

| Input | Expected | Result |
|---|---|---|
| `"Is Target cheaper than you?"` | Blocked | ✅ Blocked |
| `"What is my internal customer ID?"` | Blocked | ✅ Blocked |
| `"Do you accept cryptocurrency?"` | Blocked | ✅ Blocked |
| `"What colour t-shirts do you sell?"` | Allowed | ✅ Allowed |
| `"I hate this store and everyone in it"` | Blocked | ⚠️ Not blocked |

**Hate content note:** `"I hate this store"` scored below the HIGH threshold — the filter
targets genuine hate speech, not colloquial frustration. Options if you want this blocked:
- Add `"I hate"` to the word filter (blunt, always blocks)
- Lower content filter to MEDIUM (may increase false positives)

---

## Lessons Learned

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `ValidationException` on `create_guardrail` for PROMPT_ATTACK | `outputStrength` is not valid for `PROMPT_ATTACK` | Set `'outputStrength': 'NONE'` or omit it entirely — only `inputStrength` applies |
| 2 | Topic definition `ValidationException` — exceeds max length | Bedrock enforces a character limit on topic definitions | Keep definitions concise; put verbose examples in the `examples` list instead |
| 3 | Denied topic not firing | Definition too vague | Add named examples and specific language to the definition |
| 4 | Word filter blocking legitimate messages | Word filter has no context awareness | Move borderline terms to Denied Topics instead |
