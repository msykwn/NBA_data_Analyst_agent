"""NBA データ取得ツールのエントリーポイント。

DATA_SOURCE_MODE 環境変数に応じて実装を切り替える。
- nba_api (デフォルト): nba_api ライブラリ経由（ローカル用）
- dataset: 事前取得済みデータセット経由（AgentCore Runtime 用）
"""

import os

_MODE = os.getenv("DATA_SOURCE_MODE", "nba_api")

if _MODE == "dataset":
    from src.tools.nba_tools_dataset import (
        get_player_info,
        get_player_recent_games,
        get_player_stats,
        get_position_avg_stats,
        get_team_game_log,
        get_team_standings,
    )
else:
    from src.tools.nba_tools_nba_api import (
        get_player_info,
        get_player_recent_games,
        get_player_stats,
        get_position_avg_stats,
        get_team_game_log,
        get_team_standings,
    )

__all__ = [
    "get_player_stats",
    "get_player_recent_games",
    "get_player_info",
    "get_team_standings",
    "get_team_game_log",
    "get_position_avg_stats",
]
