import json
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')

response = client.invoke_model(
    modelId='us.anthropic.claude-sonnet-4-6',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'messages': [{'role': 'user', 'content': 'Can you explain the features of Amazon Bedrock?'}],
        'max_tokens': 1024
    })
)

body = json.loads(response['body'].read())
print(body['content'][0]['text'])
print(f"\n[{body['stop_reason']} | in:{body['usage']['input_tokens']} out:{body['usage']['output_tokens']} tokens]")
