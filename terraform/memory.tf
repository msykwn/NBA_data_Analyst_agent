resource "aws_bedrockagentcore_memory" "main" {
  name                      = "nba_data_analyst_agent_memory"
  memory_execution_role_arn = aws_iam_role.agentcore_runtime.arn
  event_expiry_duration     = 90
}
