"""AgentCore Runtime へエージェントをデプロイするスクリプト。

使い方:
    aws-vault exec piyo --no-session -- uv run python scripts/deploy.py
"""

from bedrock_agentcore_starter_toolkit.operations.runtime import (
    configure_bedrock_agentcore,
    launch_bedrock_agentcore,
)
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
AGENT_NAME = "nba_data_analyst_agent"
EXECUTION_ROLE_ARN = "arn:aws:iam::335541954164:role/nba-data-analyst-agent-agentcore-runtime"
REGION = "ap-northeast-1"
ENTRYPOINT = PROJECT_ROOT / "app/nba_data_analyst_agent/main.py"


def main():
    print("=== AgentCore Runtime デプロイ ===\n")

    print("1. 設定ファイルを生成中...")
    config_result = configure_bedrock_agentcore(
        agent_name=AGENT_NAME,
        entrypoint_path=ENTRYPOINT,
        execution_role=EXECUTION_ROLE_ARN,
        region=REGION,
        deployment_type="direct_code_deploy",
        runtime_type="PYTHON_3_12",
        memory_mode="NO_MEMORY",
        requirements_file="pyproject.toml",
        non_interactive=True,
    )
    print(f"   設定ファイル: {config_result.config_path}\n")

    print("2. デプロイ中...")
    launch_result = launch_bedrock_agentcore(
        config_path=config_result.config_path,
        auto_update_on_conflict=True,
    )
    print(f"   Agent ARN: {launch_result.agent_arn}")
    print(f"   Agent ID:  {launch_result.agent_id}")
    print("\nデプロイ完了!")


if __name__ == "__main__":
    main()