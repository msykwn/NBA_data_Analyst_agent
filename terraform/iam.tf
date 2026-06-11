data "aws_caller_identity" "current" {}

# AgentCore Runtime実行ロール
resource "aws_iam_role" "agentcore_runtime" {
  name = "nba-data-analyst-agent-agentcore-runtime"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_runtime" {
  name = "nba-data-analyst-agent-agentcore-runtime"
  role = aws_iam_role.agentcore_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvoke"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.*",
          "arn:aws:bedrock:*::foundation-model/anthropic.*",
          "arn:aws:bedrock:ap-northeast-1:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          "arn:aws:bedrock:*::inference-profile/*"
        ]
      },
      {
        Sid    = "AgentCoreMemory"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:GetMemory",
          "bedrock-agentcore:CreateMemory",
          "bedrock-agentcore:RetrieveMemoryRecords",
          "bedrock-agentcore:IngestConversationEvents"
        ]
        Resource = "arn:aws:bedrock-agentcore:ap-northeast-1:${data.aws_caller_identity.current.account_id}:memory/*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:ap-northeast-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/*"
      }
    ]
  })
}