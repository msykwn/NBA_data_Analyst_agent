"""AgentCore Runtime entrypoint for the NBA data analyst agent."""

from bedrock_agentcore import BedrockAgentCoreApp

from src.agents.orchestrator import create_orchestrator

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context):
    """AgentCore Runtime invoke handler.

    Args:
        payload: {"session_id": "...", "prompt": "..."}
        context: RequestContext (session_id 等を持つ。現フェーズでは未使用)

    Returns:
        {"response": "..."} or {"error": "..."}
    """
    prompt = payload.get("prompt", "")
    if not prompt:
        return {"error": "prompt is required"}

    try:
        orchestrator = create_orchestrator()
        result = orchestrator(prompt)
        return {"response": str(result)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    app.run()