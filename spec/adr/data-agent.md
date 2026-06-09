# データ取得エージェント

<!--
このファイルは個別要件ファイルのテンプレート。
開発完了後は spec/requirements.md にマージされ、本ファイル自体は spec/adr/ へ移動して
ADR(Architecture Decision Record)として保管される。
そのため「後から読んでも、なぜその設計・実装を選んだかが追えるドキュメント」になるよう、
開発を進める過程で生じた判断とその理由を都度このファイルに追記・更新すること。
-->

## 概要

Strands Agents で実装するデータ取得エージェント。`nba_api` ツール群(#3で実装済み)を持ち、
オーケストレーターから「Agent as Tool」として呼び出される。
与えられたパラメータに対して nba_api ツールを呼び出し、結果を返すことに専念する。
AgentCore Memory には接続せず、ステートレスに保つ。

## 背景・課題

- `spec/requirements.md` 4.2節にある通り、データ取得エージェントは「NBAデータソースを呼び出し、生データを取得する」役割を担う
- `spec/architecture.md` 3.1節の方針として、オーケストレーターが配下エージェントを「Agent as Tool」として呼び出す構成を採用している
- #3 で nba_api ツール関数群を実装済みであり、それを持つエージェントをまず単独で動作確認してから、オーケストレーターへの組み込みに進む(`spec/architecture.md` 9節)
- 会話文脈の解釈(「先週」「直近5試合」等の相対表現の解決)はオーケストレーターが担うため、このエージェントは与えられた条件でAPIを呼び出すことに専念する(`spec/requirements.md` 5.5節)

## 要件

### 機能要件

- `nba_api` ツール群(#3実装済み)を Strands Agents のツールとして保持する
- オーケストレーターから Agent as Tool として呼び出せる形で定義する
- 入力: オーケストレーターからの自然言語の質問(または解釈済みのパラメータ)を受け取る
- 出力: nba_api ツールの取得結果をそのまま、または簡単に整形して返す
- AgentCore Memory には接続しない(ステートレス)
- ローカル単体での動作確認ができること
  - 例: 「レブロン・ジェームズの今シーズンの成績を教えて」に対して実データが返ること

### 非機能要件

- 特になし(学習目的のプロジェクトのため)

## 検討した選択肢

### 選択肢A: Agent as Tool パターン(Strands Agents)
- メリット: `spec/architecture.md` 3.1節で採用決定済み。オーケストレーターがツールとして呼び出せる。Strands Agentsの公式パターンと一致しており、AgentCore学習目的に合っている
- デメリット: Strands Agents の Agent as Tool の具体的な実装方法は実装時に公式ドキュメントで確認が必要

### 選択肢B: 通常の関数としてオーケストレーターから直接呼び出す
- メリット: シンプル。エージェントとして動作させる必要がない場合は十分
- デメリット: LLMによる推論・ツール選択の恩恵が得られない。将来的にエージェントとして独立させにくい

## 採用した方針と理由

選択肢Aを採用。`spec/architecture.md` 3.1節で決定済みの方針と一致し、AgentCore学習という目的にも最も合っている。

## 状態

実装完了・動作確認済み(2026-06-10時点)

動作確認コマンド:
```bash
aws-vault exec piyo --no-session -- uv run python -m src.agents.data_agent
```

## この決定によって生じる影響

### 良い影響
- データ取得エージェントがステートレスなため、設計がシンプルで単体テストしやすい
- Agent as Tool パターンにより、将来的に個別 AgentCore Runtime への分離も容易(`spec/architecture.md` 11節)

### 悪い影響・リスク・前提条件
- Strands Agents の Agent as Tool の具体的な実装パターンは実装時に公式ドキュメントで確認が必要
- #3 の nba_api ツール群が実装済みであることが前提

## 仕様変更の経緯

### AWS認証方式の変更(2026-06-10)

- **変更前**: `boto3.Session(profile_name="piyo")` でプロファイルを直接指定する方式、または `AWS_PROFILE=piyo` 環境変数を試みた
- **変更理由**: `~/.aws/credentials` には直接認証情報が記載されておらず、aws-vault で管理されているため、boto3 のプロファイル直接指定では `NoCredentialsError` が発生した
- **変更後**: `aws-vault exec piyo --no-session -- uv run python -m src.agents.data_agent` として実行する。boto3 セッションの直接指定は不要で、aws-vault が環境変数経由で認証情報を注入するため Strands Agents のデフォルト認証チェーンが機能する

### nba_tools.py の `DEFAULT_SEASON` 未定義バグ修正(2026-06-10)

- `get_team_game_log` と `get_position_avg_stats` のデフォルト引数に `DEFAULT_SEASON` を使っていたが、この定数は定義されていなかった
- `""` をデフォルトにして関数内で `season or _current_season()` にフォールバックする形に統一した
