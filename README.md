# AWS Bedrock Experiments

Learning and experimenting with AWS Bedrock and the Anthropic Claude models via `boto3`.

## Getting Started

1. **Use the pinned Python version.** This project targets the `bedrock-3.13.3` pyenv
   environment (see `.python-version`). If you use `pyenv`:

   ```bash
   pyenv install 3.13.3   # if not already installed
   pyenv virtualenv 3.13.3 bedrock-3.13.3
   ```

   Any Python 3.10+ environment works too — the pin just keeps this repo's env named
   consistently.

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set the Bedrock bearer token** (see [Authentication](#authentication) below):

   ```bash
   export AWS_BEARER_TOKEN_BEDROCK=your_token_here
   ```

4. **First-time model access** — if you haven't invoked Claude on Bedrock in this
   account before, complete the one-time use-case form (see
   [Model Access](#model-access-first-time-setup) below) before running any notebook.

5. **Launch Jupyter and start with `bedrock_direct_calls.ipynb`** — it only needs the
   bearer token and covers chat, streaming, tool use, and guardrails end to end:

   ```bash
   jupyter lab
   ```

6. **Then try `bedrock_agent_client.ipynb`** — this one talks to a deployed Bedrock
   Agent and needs a _separate_ credential setup (real AWS IAM credentials, not the
   bearer token). See the callout in [Authentication](#authentication).

## Prerequisites

- Python 3.10+ (project is pinned to `bedrock-3.13.3` via `.python-version`)
- Dependencies from `requirements.txt` (`boto3`, `jupyterlab`)
- An `AWS_BEARER_TOKEN_BEDROCK` credential for direct model calls
- A working AWS profile/IAM credentials (e.g. via `aws configure`) if you want to run
  `bedrock_agent_client.ipynb`

## Authentication

This project authenticates direct model calls via a single environment variable:

```bash
export AWS_BEARER_TOKEN_BEDROCK=your_token_here
```

Standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are **not** used for those calls.
The bearer token is the only credential needed for `bedrock-runtime` inference.

> **Limitation — Bedrock Agents:** `AWS_BEARER_TOKEN_BEDROCK` only works for
> `bedrock-runtime` / `bedrock`. `bedrock-agent-runtime` and `bedrock-agent` (used by
> `bedrock_agent_client.ipynb`) don't support bearer-token auth at all — their botocore
> service definitions only declare `aws.auth#sigv4`. To run that notebook you need a
> real AWS profile or access key with permission to invoke the agent, e.g.:
>
> ```bash
> aws configure   # or set AWS_PROFILE to a profile with valid credentials
> ```
>
> If you see `InvalidClientTokenId` or `UnrecognizedClientException` — "The security
> token included in the request is invalid" — from that notebook, this is almost always
> the cause: no IAM credentials configured, or a temporary/session credential that has
> expired. Verify with:
>
> ```bash
> aws sts get-caller-identity
> ```
>
> If credentials were just refreshed, **restart the Jupyter kernel** — boto3 caches
> resolved credentials for the life of the process, so re-running cells alone won't pick
> up new ones.

## Model Access (first-time setup)

The Model access page has been retired — models are enabled automatically on first
invocation. For Anthropic models, first-time users must submit a use-case form before
invoking via code:

1. Open **Bedrock → Model catalog** and select Claude Sonnet 4.6
2. Open it in the playground — a use-case form appears
3. Fill it out and submit
4. Wait up to 15 minutes; models are then enabled automatically on first invocation

## Project Files

| File                          | Description                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| `bedrock-first-request.py`    | Minimal script — invoke Claude Sonnet 4.6 via `bedrock-runtime`                                |
| `bedrock_direct_calls.ipynb`  | Notebook — direct boto3 inference: chat, streaming, tool use, guardrails                       |
| `bedrock_agent_client.ipynb`  | Notebook — client for the deployed `returns-agent` (needs IAM credentials, see Authentication) |
| `bedrock-agent-guide.md`      | Step-by-step guide: IAM role, Lambda, Bedrock Agent, versioning                                |
| `bedrock-guardrails-guide.md` | Step-by-step guide: content filters, denied topics, word filters, PII                          |
| `bedrock.md`                  | Lessons learned — gotchas with auth, model IDs, response parsing                               |

## Running the script

```bash
python bedrock-first-request.py
```

## Starting the Jupyter server

```bash
jupyter lab
```

This opens the notebook UI in your browser at `http://localhost:8888`. Open
`bedrock_direct_calls.ipynb` or `bedrock_agent_client.ipynb` from there.

To run on a specific port or without opening a browser:

```bash
jupyter lab --port 8889 --no-browser
```

> **Note on `bedrock_agent_client.ipynb` Section 7 (Interactive REPL):** that cell
> blocks on `input()` for a live back-and-forth. Run it directly in a Jupyter session
> where you can type responses — it isn't something you can drive from a script or
> automated tool.

## Model IDs

| Model             | ID                               |
| ----------------- | -------------------------------- |
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` |

The `us.` prefix is required — it is the cross-region inference profile for Claude 4.x
models.

## Key boto3 Notes

- Client for inference: `bedrock-runtime` (not `bedrock`)
- Required request field: `anthropic_version: 'bedrock-2023-05-31'`
- Response body is a stream — call `.read()` before `json.loads()`
- Agent invocation uses `bedrock-agent-runtime` and returns an EventStream, and requires
  IAM SigV4 credentials (not the bearer token — see Authentication)

## Deployed Resources

- **Agent:** `returns-agent` — customer returns processing, backed by a Lambda function
- **Alias:** `prod` → Version 2 (with guardrail attached)
- **Lambda:** `returns-processor` (Python 3.12, us-east-1)
- **Guardrail:** `test-guard` (ID: `32labz8mu0fe`) — content filters, denied topics, word filters
