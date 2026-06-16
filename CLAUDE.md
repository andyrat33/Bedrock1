# Bedrock1 Project

## Purpose
Learning and experimenting with AWS Bedrock and the Anthropic Claude models via boto3.

## Authentication
Uses `AWS_BEARER_TOKEN_BEDROCK` environment variable — this is the only credential needed. Standard AWS IAM env vars (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) are not used in this setup.

## Model Access Setup
The Model access page has been retired. Models are automatically enabled on first invocation.
For Anthropic models, first-time users must fill out the use case form: go to the Model catalog, open the model in the playground, and submit the form from there. Wait up to 15 minutes after submitting before invoking via code.

## Model IDs
- Claude Sonnet 4.6: `us.anthropic.claude-sonnet-4-6`
- The `us.` prefix is required — it's the cross-region inference profile for Claude 4.x models

## boto3 Usage Notes
- Client: `bedrock-runtime` (not `bedrock`) for inference
- Required field: `anthropic_version: 'bedrock-2023-05-31'`
- Response body is a stream: call `.read()` before `json.loads()`

## Guardrails
Guardrail `test-guard`: ID `32labz8mu0fe`, version `1`, region `us-east-1`.

Two boto3 APIs:
- `client.apply_guardrail(guardrailIdentifier, guardrailVersion, source, content)` — test without model
- `client.invoke_model(..., guardrailIdentifier=..., guardrailVersion=..., trace='ENABLED')` — inline enforcement

Detect block via HTTP header: `response['ResponseMetadata']['HTTPHeaders']['x-amzn-bedrock-guardrail-action'] == 'INTERVENED'`

Gotcha: when guardrail blocks at INPUT phase (before model runs), response body has **no `usage` or `stop_reason`**. Use `.get()` with defaults.

Trace data (when `trace='ENABLED'`): `response_body['amazon-bedrock-trace']['guardrail']`

## Notebooks
- `bedrock_direct_calls.ipynb` — direct boto3 inference: chat, streaming, tool use, guardrails (Sections 1–7)
- `bedrock_agent_client.ipynb` — Bedrock Agents client for the returns-agent
