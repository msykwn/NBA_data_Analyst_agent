"""Orchestrator agent that coordinates data and analysis agents."""

from datetime import date

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from src.agents.analysis_agent import analysis_agent
from src.agents.data_agent import data_agent


def _build_system_prompt() -> str:
    today = date.today().isoformat()
    return f"""あなたはNBAデータアナリストエージェントの司令塔です。
ユーザーからの質問を解釈し、配下の専門エージェントに処理を委譲して、最終的な回答を生成してください。

今日の日付: {today}

## 配下エージェント

- **data_agent**: NBAの選手・チーム・試合などの統計データを取得する専門エージェント
- **analysis_agent**: 取得したデータをもとに比較・ランキング・要約などの分析を行う専門エージェント

## 振り分けルール

### パターン1: 単純な照会（「成績を教えて」「どこのチームに所属してる?」など）
1. data_agent にデータ取得を依頼する
2. 取得結果を整理してユーザーに回答する（analysis_agent への委譲は不要）

### パターン2: 明示的な比較・ランキング（「AとBを比較して」「上位5人は?」など）
1. data_agent に必要なデータ取得を依頼する
2. 取得したデータを analysis_agent に渡して比較・ランキング分析を依頼する
3. analysis_agent の分析結果をユーザーに回答する

### パターン3: 定型的な傾向質問（「最近調子良い?」「3Pが得意?」「安定してる?」など）
1. data_agent に今シーズン成績・直近試合データ・必要に応じてポジション別平均データの取得を依頼する
2. 取得したデータを analysis_agent に渡して傾向分析を依頼する
3. analysis_agent の分析結果をユーザーに回答する

## 期間表現の解釈

「先週」「直近5試合」「最近1ヶ月」のような相対的な期間表現は、
今日の日付（{today}）を基準に具体的な日付範囲や試合数に変換してから、配下エージェントに渡してください。
- 「先週」→ 先週月曜〜日曜の日付範囲
- 「直近N試合」→ 最新からN試合分
- 「最近1ヶ月」→ 今日から30日前〜今日の日付範囲

## 注意事項

- 回答は日本語で行ってください
- データが取得できない場合や質問の意図が不明確な場合は、その旨をユーザーに伝えてください
- 選手名・チーム名の揺れ（表記ゆれ）は data_agent が候補リストを返すため、ユーザーに確認してください
- data_agent と analysis_agent は**必ず1回ずつ順番に呼び出してください**。複数選手のデータが必要な場合も、1回の data_agent 呼び出しで全選手をまとめて取得するよう依頼してください。同じエージェントを並列・同時に呼び出してはいけません
"""


def create_orchestrator() -> Agent:
    """オーケストレーターエージェントのインスタンスを生成して返す。

    呼び出しごとに新しいインスタンスを生成することで、
    会話履歴の汚染と data_agent への並列呼び出し競合を防ぐ。
    """
    return Agent(
        name="orchestrator",
        description="NBAデータアナリストの司令塔エージェント。ユーザーの質問を解釈し、データ取得・分析エージェントへ処理を委譲して最終回答を生成する。",
        system_prompt=_build_system_prompt(),
        tools=[
            data_agent.as_tool(),
            analysis_agent.as_tool(),
        ],
        tool_executor=SequentialToolExecutor(),
    )


if __name__ == "__main__":
    print("=== オーケストレーターエージェント 動作確認 ===\n")

    questions = [
        "レブロン・ジェームズの今シーズンの成績を教えてください。",
        "ステフィン・カリーとニコラ・ヨキッチの今シーズン成績を比較してください。",
        "レブロン・ジェームズは最近調子良いですか？",
    ]

    for question in questions:
        orchestrator = create_orchestrator()
        print(f"質問: {question}")
        result = orchestrator(question)
        print(f"回答: {result}\n")
        print("-" * 60 + "\n")
