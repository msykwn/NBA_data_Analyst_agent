# AgentCore Runtime デプロイ

<!--
このファイルは個別要件ファイルのテンプレート。
開発完了後は spec/requirements.md にマージされ、本ファイル自体は spec/adr/ へ移動して
ADR(Architecture Decision Record)として保管される。
そのため「後から読んでも、なぜその設計・実装を選んだかが追えるドキュメント」になるよう、
開発を進める過程で生じた判断とその理由を都度このファイルに追記・更新すること。
-->

## 概要

Strands Agentsで実装したマルチエージェント（オーケストレーター・データ取得・分析）を AWS Bedrock AgentCore Runtime に乗せ、REST API として公開できるようにする。

**スコープ（やること）:**
- `bedrock-agentcore` パッケージの追加
- AgentCore Runtime 用エントリーポイント（`main.py`）の作成
- デプロイ手順の整備（`agentcore deploy` による手動デプロイ）

**スコープ（やらないこと）:**
- AgentCore Memory との連携（別フェーズ）
- フロントエンド（React）の実装
- CI/CD による自動デプロイ

## 背景・課題

本プロジェクトの主目的は AWS Bedrock AgentCore の学習であり、エージェントロジックの実装だけでなく AgentCore Runtime 上でエージェントを実際に動かす経験を積むことが狙い。

ローカルでの Strands Agents 単体動作確認（`orchestrator.py` の `__main__`）と並行して、AgentCore Runtime へのデプロイ準備を進める。

**前提・制約:**
- Terraform によるインフラリソース（IAMロール、AgentCore Memory）は `apply` 済みで、AWSリソースは構築完了
- エージェントコードのデプロイは Terraform の管理範囲外（`spec/architecture.md` 8節・`spec/infrastructure.md` 4.3節の方針）
- AWS認証には aws-vault を使用（`aws-vault exec piyo --no-session --` 経由）

## 要件

### 機能要件

- AgentCore Runtime の HTTP エンドポイント（`POST /invocations`）経由でオーケストレーターエージェントを呼び出せる
- 入力形式: `{"session_id": "...", "prompt": "..."}`
  - `session_id`: 将来のMemory連携に備えて受け取るが、現フェーズでは使用しない
  - `prompt`: ユーザーの質問テキスト
- 出力形式: `{"response": "..."}` （エージェントの回答テキスト）
- エラー時は `{"error": "..."}` を返す
- `GET /ping` によるヘルスチェックに応答する

### 非機能要件

- 特になし（学習目的のため、パフォーマンス・可用性等の厳密な要件は設けない）

## 検討した選択肢

### エントリーポイントの配置場所

#### 選択肢A: `src/main.py`
- メリット: 既存の `src/` にまとまり、ディレクトリが増えない
- デメリット: AgentCore CLI（`agentcore deploy`）が期待する `app/<AgentName>/main.py` の規約と異なる

#### 選択肢B: `app/nba_data_analyst_agent/main.py`
- メリット: AgentCore CLI の規約に沿った構造で整合性が高い
- デメリット: ディレクトリが増える

### デプロイコマンド

#### 選択肢A: `agentcore deploy`（Node.js CLI）
- メリット: 公式CLIで操作がシンプル
- デメリット: IAMロール等を自動生成しようとするため、Terraformで管理している既存リソースと競合する可能性がある

#### 選択肢B: `bedrock-agentcore-starter-toolkit`（Python SDK）
- メリット: 既存IAMロールのARNを明示的に指定でき、Terraformとの棲み分けが明確になる
- デメリット: CLIより設定が若干煩雑
- 実装上の判断: `configure_bedrock_agentcore` + `launch_bedrock_agentcore` 関数を `scripts/deploy.py` にまとめ、`aws-vault exec piyo --no-session -- uv run python scripts/deploy.py` で実行する形とした

## 採用した方針と理由

- **エントリーポイントの配置**: `app/nba_data_analyst_agent/main.py`（選択肢B）を採用。AgentCore CLI の規約に沿った構造にすることで、将来的にCLIを使う場合にも整合性を保てる。
- **デプロイコマンド**: `bedrock-agentcore-starter-toolkit`（Python SDK、選択肢B）を採用。TerraformでIAMロール等を管理している都合上、既存リソースのARNを明示的に指定できるPython SDKの方がTerraformとの役割分担が明確になる。

## 状態

実装完了（2026-06-10）

## この決定によって生じる影響

**良い影響:**
- AgentCore Runtime の REST API 経由でエージェントを呼び出せるようになり、将来のフロントエンド接続・Memory組み込みの土台ができる
- Terraform（インフラ）と Python SDK（エージェントデプロイ）の役割分担が明確に保たれる

**リスク・懸念点:**
- `bedrock-agentcore-starter-toolkit` は GA 間もない新しいパッケージのため、ドキュメント・サンプルが薄く、実装中に API 仕様が想定と異なるケースが出る可能性がある
- 実装中に判明した制約・トレードオフはこのセクションに随時追記する

## 仕様変更の経緯

<!--
開発途中で仕様変更が発生した場合、変更前の内容・変更理由・変更後の内容を時系列で追記する。
変更が無ければ「なし」のままでよい。
-->

なし