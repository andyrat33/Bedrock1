# AWS Bedrock Experiments

Learning and experimenting with AWS Bedrock and the Anthropic Claude models via `boto3`.

## Prerequisites

- Python 3.10+
- `boto3` installed (`pip install boto3`)
- `jupyter` installed (`pip install jupyter`) — for notebooks
- An `AWS_BEARER_TOKEN_BEDROCK` credential (see Authentication below)

## Authentication

This project authenticates via a single environment variable:

```bash
export AWS_BEARER_TOKEN_BEDROCK=your_token_here
```

Standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are **not** used. The bearer token is the only credential needed for `bedrock-runtime` inference calls.

> **Note:** `AWS_BEARER_TOKEN_BEDROCK` covers `bedrock-runtime` only. Invoking agents via
> `bedrock-agent-runtime` requires a standard AWS profile or IAM credentials instead.

## Model Access (first-time setup)

For Anthropic models, submit the use-case form before invoking via code:

1. Open **Bedrock → Model catalog** and select Claude Sonnet 4.6
2. Open it in the playground — a use-case form appears
3. Fill it out and submit
4. Wait up to 15 minutes; models are then enabled automatically on first invocation

## Project Files

| File | Description |
|---|---|
| `bedrock-first-request.py` | Minimal script — invoke Claude Sonnet 4.6 via `bedrock-runtime` |
| `bedrock_agent_client.ipynb` | Jupyter notebook for invoking the deployed returns agent |
| `bedrock-agent-guide.md` | Step-by-step guide: IAM role, Lambda, Bedrock Agent, versioning |
| `bedrock-guardrails-guide.md` | Step-by-step guide: content filters, denied topics, word filters, PII |
| `bedrock.md` | Lessons learned — gotchas with auth, model IDs, response parsing |

## Running the script

```bash
python bedrock-first-request.py
```

## Starting the Jupyter server

```bash
jupyter notebook
```

This opens the notebook UI in your browser at `http://localhost:8888`. Open `bedrock_agent_client.ipynb` from there.

To run on a specific port or without opening a browser:

```bash
jupyter notebook --port 8889 --no-browser
```

To run JupyterLab instead:

```bash
jupyter lab
```

## Model IDs

| Model | ID |
|---|---|
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` |

The `us.` prefix is required — it is the cross-region inference profile for Claude 4.x models.

## Key boto3 Notes

- Client for inference: `bedrock-runtime` (not `bedrock`)
- Required request field: `anthropic_version: 'bedrock-2023-05-31'`
- Response body is a stream — call `.read()` before `json.loads()`
- Agent invocation uses `bedrock-agent-runtime` and returns an EventStream

## Deployed Resources

- **Agent:** `returns-agent` — customer returns processing, backed by a Lambda function
- **Alias:** `prod` → Version 2 (with guardrail attached)
- **Lambda:** `returns-processor` (Python 3.12, us-east-1)
- **Guardrail:** `test-guard` (ID: `32labz8mu0fe`) — content filters, denied topics, word filters
