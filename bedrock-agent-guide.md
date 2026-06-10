# AWS Bedrock Returns Agent — Setup Guide

## Overview
A customer-facing returns-processing agent built with AWS Bedrock Agents + Lambda.
The agent collects an order number, invokes a Lambda function to process the return,
and responds conversationally with the outcome.

**Model:** Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`)
**Region:** us-east-1

---

## Part 1 — IAM Role

### 1.1 Create the Role

1. Open **IAM → Roles → Create role**
2. Trusted entity type: **AWS service**
3. Use case: **Bedrock → Bedrock Agent**
4. Click **Next**

> **Note:** When you create the agent in the console, AWS can auto-create this role for you
> (named `AmazonBedrockExecutionRoleForAgents_XXXXXXXXX`). If you let it do that, you still
> need to add the `lambda:InvokeFunction` permission manually — it is NOT included by default
> (see step 1.3). Skipping this causes a silent failure where the agent calls Lambda but the
> request is denied.

### 1.2 Replace the Trust Policy

After creation → **Trust relationships** tab → **Edit trust policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "bedrock.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "aws:SourceAccount": "YOUR_ACCOUNT_ID" }
      }
    }
  ]
}
```

### 1.3 Add Permissions (inline policy)

**Add permissions → Create inline policy → JSON:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-sonnet-4-6"
    },
    {
      "Sid": "LambdaInvoke",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:returns-processor"
    }
  ]
}
```

- Policy name: `bedrock-agent-permissions`
- Role name: `bedrock-returns-agent-role`

---

## Part 2 — Model Access

> Claude Sonnet 4.6 access was already granted in this account (done in a prior session).
> Skip this step unless using a different model.

**To enable a new Anthropic model:**
1. Bedrock → Model catalog → find the model
2. Open in playground → fill out the Anthropic use case form
3. Wait up to 15 minutes → status changes to **Access granted**

---

## Part 3 — Create the Bedrock Agent

**Bedrock → Agents → Create agent**

| Field | Value |
|---|---|
| Agent name | `returns-agent` |
| Agent resource role | `bedrock-returns-agent-role` |
| Model | Claude Sonnet 4.6 |

### System Prompt (paste into "Instructions for the Agent")

```
You are a friendly customer service agent for an online retailer. Your job is to help
customers initiate product returns.

Rules:
- Greet the customer warmly when they first contact you.
- If the customer has not provided an order number, ask for it before doing anything else.
- Order numbers are numeric and between 6 and 10 digits. If the format looks wrong, ask
  the customer to double-check it.
- Confirm the order number back to the customer before initiating any return.
- After a successful return, inform the customer that a prepaid return label will be sent
  to the email address on their account within 24 hours.
- If the return fails, apologise and offer to escalate to a human agent.
- Never invent or assume order details. Only report what the system tells you.
- Keep responses concise and friendly.
```

Click **Save** (do NOT click Prepare yet — add the action group first).

---

## Part 4 — Lambda Function

### 4.1 Create the Function

**Lambda → Create function → Author from scratch**

| Field | Value |
|---|---|
| Function name | `returns-processor` |
| Runtime | Python 3.12 |

### 4.2 Handler Code

> **Paste pitfall:** Copying from a markdown doc often adds a leading space to every line.
> Python treats indentation as syntax, so `·import json` (with a leading space) causes an
> `unexpected indent` error before the function even runs. Always select-all and delete before
> pasting, and verify Runtime settings shows `lambda_function.lambda_handler`.

> **Response format:** Bedrock requires `messageVersion` and a `response` wrapper in the
> Lambda return value. Returning the payload at the top level causes a
> `dependencyFailedException` even though the Lambda itself exits cleanly.

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event received: %s", json.dumps(event))

    action_group = event.get('actionGroup', '')
    function     = event.get('function', '')
    parameters   = {p['name']: p['value'] for p in event.get('parameters', [])}

    # Match on the parameter rather than the function name — the console can assign
    # an unexpected name to the function (e.g. the action group name) depending on
    # how the action group was created.
    if 'order_number' in parameters:
        order_number = parameters.get('order_number', '').strip()

        # Replace this block with a real DB / API call
        if order_number.isdigit() and 6 <= len(order_number) <= 10:
            message = (
                f"Return successfully initiated for order {order_number}. "
                "A prepaid return label will be sent to the email on your account "
                "within 24 hours."
            )
        else:
            message = (
                f"Order number '{order_number}' could not be found. "
                "Please double-check the number and try again."
            )
    else:
        message = "I need an order number to process a return. Please provide your order number."

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {"body": message}
                }
            }
        }
    }
```

Click **Deploy**.

### 4.3 Add Resource-Based Policy

**Configuration → Permissions → Add permissions (Resource-based policy):**

| Field | Value |
|---|---|
| Statement ID | `allow-bedrock-invoke` |
| Principal | `bedrock.amazonaws.com` |
| Action | `lambda:InvokeFunction` |
| Condition key | `aws:SourceAccount` |
| Condition value | `YOUR_ACCOUNT_ID` |

---

## Part 5 — Action Group

**Bedrock → Agents → returns-agent → Working draft → Action groups → Add**

| Field | Value |
|---|---|
| Action group name | `returns-action-group` |
| Action group type | **Define with function details** |
| Lambda function | `returns-processor` ($LATEST) |

### Function Definition

| Field | Value |
|---|---|
| Name | `process_return` |
| Description | Initiates a product return for the given order number |

**Parameter:**

| Field | Value |
|---|---|
| Name | `order_number` |
| Type | String |
| Required | Yes |
| Description | The customer's numeric order number (6–10 digits) |

Click **Save and exit**.

---

## Part 6 — Prepare, Version, and Alias

### Prepare

After any change to the agent, you must prepare it before testing or deploying.

**Bedrock → Agents → returns-agent → Prepare**

Wait for status: **Prepared**

**Test in the console panel:**
> *"Hi, I'd like to return my order 987654"*

The agent should confirm the order number, call `process_return`, and report the outcome.

### Create a Version (immutable snapshot)

**Agent overview → Create version**

| Field | Value |
|---|---|
| Description | `v1 - initial returns agent` |

### Create an Alias (production pointer)

**Aliases → Create alias**

| Field | Value |
|---|---|
| Alias name | `prod` |
| Route traffic to | Version 1 |

> Always use the **alias ARN** in application code — never the agent ARN directly.
> To deploy a new version, update the alias. To roll back, point it to the previous version.

---

## Invoking the Agent via boto3

> Use `bedrock-agent-runtime` (not `bedrock-runtime`). The response is an EventStream —
> iterate over `response['completion']` and decode each `chunk`. Use an AWS profile or
> ensure credentials are in the environment; `AWS_BEARER_TOKEN_BEDROCK` is Bedrock-inference
> only and does not cover `bedrock-agent-runtime`.

```python
import boto3, uuid

session = boto3.Session(profile_name='YOUR_PROFILE')  # or omit if using env credentials
client = session.client('bedrock-agent-runtime', region_name='us-east-1')

response = client.invoke_agent(
    agentId='YOUR_AGENT_ID',       # find in Bedrock → Agents → Agent overview
    agentAliasId='YOUR_ALIAS_ID',  # use TSTALIASID for the test alias, or your prod alias ID
    sessionId=str(uuid.uuid4()),   # unique per conversation; reuse the same ID for multi-turn
    inputText="I need to return order 123456"
)

for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode(), end='')
```

---

## Rollout Workflow

```
Edit agent → Prepare → Test in console → Create new version → Update alias to new version
```

To roll back instantly: point the alias back to the previous version.

---

## Lessons Learned (from first deployment)

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `Runtime.UserCodeSyntaxError: unexpected indent line 1` | Pasting from markdown added a leading space to every line | Select-all delete before pasting; verify with CloudWatch logs |
| 2 | Same syntax error after re-paste | Function named `handler` not `lambda_handler` — mismatch with Runtime settings | Check **Runtime settings → Handler** equals `lambda_function.lambda_handler` |
| 3 | `dependencyFailedException: error processing Lambda response` | Lambda response missing `messageVersion` and `response` wrapper | Return `{"messageVersion": "1.0", "response": {...}}` |
| 4 | Agent returns "Unknown function" | Console quick-start sets the function name to the action group name, not `process_return` | Match on parameter presence (`order_number in parameters`) rather than the function name string |
| 5 | Agent can't invoke Lambda even with correct code | Auto-created IAM role has no `lambda:InvokeFunction` permission | Add inline policy with `lambda:InvokeFunction` on the Lambda ARN |
