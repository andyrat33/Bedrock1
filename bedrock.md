# AWS Bedrock Lessons Learned

## 1. Model Access — Anthropic Use Case Form
- The Model access page has been retired; models are automatically enabled on first invocation
- For **Anthropic models**, first-time users must submit use case details
- Error if skipped: `ResourceNotFoundException: Model use case details have not been submitted`
- **Actual process followed:**
  1. Go to Bedrock → Model catalog
  2. Select Claude Sonnet 4.6
  3. Open it in the playground
  4. Fill out the Anthropic use case form when prompted
  5. Wait up to 15 minutes, then invoke via code
- Account admins can restrict access via IAM policies and Service Control Policies

## 2. Authentication Uses AWS_BEARER_TOKEN_BEDROCK
- This project authenticates via `AWS_BEARER_TOKEN_BEDROCK` environment variable
- Without it: `UnrecognizedClientException: The security token included in the request is invalid`
- Standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are not used in this setup

## 3. Model ID Format for Claude 4.x
- Must use the cross-region inference profile prefix: `us.anthropic.claude-sonnet-4-6`
- The `us.` prefix is required for Claude 4.x models on Bedrock

## 4. boto3 Client
- Use `bedrock-runtime` client for inference (not `bedrock`)
- `bedrock` client is for management operations (listing models, managing access, etc.)

## 5. Request Body Requirements
- `anthropic_version: 'bedrock-2023-05-31'` is mandatory
- Messages follow the standard Anthropic messages API format

## 6. Reading the Response
- `response['body']` is a streaming object
- Must call `.read()` before passing to `json.loads()`
- Response structure: `body['content'][0]['text']` for the text, `body['usage']` for token counts

## 7. Pylance boto3 Warning
- IDE may show `Import "boto3" could not be resolved` — this is a Pylance type stub issue
- Does not affect execution
