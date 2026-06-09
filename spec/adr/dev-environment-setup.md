# Python開発環境のセットアップ

<!--
このファイルは個別要件ファイルのテンプレート。
開発完了後は spec/requirements.md にマージされ、本ファイル自体は spec/adr/ へ移動して
ADR(Architecture Decision Record)として保管される。
そのため「後から読んでも、なぜその設計・実装を選んだかが追えるドキュメント」になるよう、
開発を進める過程で生じた判断とその理由を都度このファイルに追記・更新すること。
-->

## 概要

uv + Python 3.12 を用いてローカルのPython開発環境を構築する。
`pyproject.toml` を作成し、Strands Agents・nba_api・boto3 を依存パッケージとして追加する。
AWS CLIプロファイルの設定やBedrockへの疎通確認はスコープ外とする。

## 背景・課題

- 本プロジェクトではエージェントロジックをPythonで実装する(`spec/architecture.md` 3節・9節)
- エージェントフレームワークとして Strands Agents を採用しており、その前提となる実行環境が必要
- データ取得エージェントが `nba_api` を使って stats.nba.com からデータを取得する(`spec/requirements.md` 6節・`spec/architecture.md` 5節)
- Bedrock呼び出しには `boto3` が必要(Strands Agentsの依存含む)
- モダンな構成(`pyproject.toml` ベース)に触れることも学習目的の一つ(`spec/architecture.md` 9.1節)

## 要件

### 機能要件

- uv で Python 3.12 の仮想環境を作成・管理できること
- `pyproject.toml` に以下の依存パッケージが定義されていること
  - `strands-agents`
  - `nba_api`
  - `boto3`
- `uv sync` 一発で依存パッケージがインストールできること
- `uv run python -c "import strands; import nba_api; import boto3"` がエラーなく通ること

### 非機能要件

- 特になし(学習目的のプロジェクトのため)

## 検討した選択肢

パッケージ管理ツールは `spec/architecture.md` 9.1節で **uv を採用** と決定済みのため、比較は省略する。

## 採用した方針と理由

uv + `pyproject.toml` によるパッケージ管理を採用。
採用理由は `spec/architecture.md` 9.1節に記載の通り:
- 高速なインストール・実行が可能
- AWS・Strands Agents 関連の最新ドキュメント/サンプルでも採用例が増えている
- モダンな構成に触れる学習価値がある

## 状態

採用・完了(2026-06-10)

## この決定によって生じる影響

### 良い影響
- `uv sync` 一発で環境を再現できるため、以降の開発をすぐに始められる
- `pyproject.toml` ベースの構成により、将来的なパッケージ追加・バージョン管理がシンプル

### 悪い影響・前提条件
- uv が未インストールの場合は先に `brew install uv` 等でインストールが必要
- AWS CLIプロファイル(`~/.aws/credentials`)が設定済みであることが前提(このタスクのスコープ外)

## 仕様変更の経緯

なし