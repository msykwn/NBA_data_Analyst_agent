"""Data fetching agent for NBA statistics."""

from strands import Agent

from src.tools.nba_tools import (
    get_player_info,
    get_player_recent_games,
    get_player_stats,
    get_position_avg_stats,
    get_team_game_log,
    get_team_standings,
)

SYSTEM_PROMPT = """あなたはNBAデータ取得の専門エージェントです。

与えられた質問に対して、適切なツールを呼び出してNBAの統計データを取得し、結果をそのまま返してください。
データの解釈や分析は行わず、取得したデータを正確に報告することに専念してください。

注意事項:
- 選手名・チーム名が見つからない場合は、候補リストをそのままユーザーに返してください
- シーズンの指定がない場合は、現在のシーズンを自動判定して使用してください
"""

data_agent = Agent(
    name="data_agent",
    description="NBAの選手・チーム・試合などの統計データを外部APIから取得する専門エージェント。選手名やチーム名を受け取り、スタッツ・順位・試合結果などのデータを返す。",
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_player_stats,
        get_player_recent_games,
        get_player_info,
        get_team_standings,
        get_team_game_log,
        get_position_avg_stats,
    ],
)


if __name__ == "__main__":
    print("=== データ取得エージェント 動作確認 ===\n")

    questions = [
        "レブロン・ジェームズの今シーズンの成績を教えてください。",
        "ニコラ・ヨキッチの直近5試合のスタッツを教えてください。",
        "NBAウェスタンカンファレンスの現在の順位を教えてください。",
    ]

    for question in questions:
        print(f"質問: {question}")
        result = data_agent(question)
        print(f"回答: {result}\n")
        print("-" * 60 + "\n")
