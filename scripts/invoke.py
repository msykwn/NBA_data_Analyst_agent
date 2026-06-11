import boto3
import json
import uuid

AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:ap-northeast-1:335541954164:runtime/nba_data_analyst_agent-k3n4MwEfMs"
SESSION_ID = str(uuid.uuid4()) + "-verify"  # 33文字以上必要

prompt = "LeBron Jamesの2024-25シーズンの平均得点を教えて"

client = boto3.client("bedrock-agentcore", region_name="ap-northeast-1")
payload = json.dumps({"prompt": prompt})

print(f"Session ID : {SESSION_ID}")
print(f"Prompt     : {prompt}")
print("---")

response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    runtimeSessionId=SESSION_ID,
    payload=payload,
)

response_body = response["response"].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)
