# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

NBAのデータを分析できるチャット型AIエージェントを作成する。AWS Bedrock AgentCore の学習を主目的としており、AgentCore上でエージェントを構築・運用する経験を積むことが狙い。
AIエージェントの作成を学習したいので複数のエージェントを動かして回答を行うようなシステムを作りたい。

現時点ではまだ実装前で、設計・方針整理の段階。READMEと本ファイル以外にソースコードは存在しない。

## 想定アーキテクチャ

```
[ユーザー (チャットUI)]
        ↓
[React フロントエンド]  ※後回し。まずはCLI/API経由での動作確認を優先
        ↓
[Python バックエンド]
        ↓
[AWS Bedrock AgentCore Runtime]  … エージェントのホスティング・実行基盤
        └─ Memory   … 会話履歴(短期記憶)・ユーザーの嗜好や要約(長期記憶)の保持
        ↓
[NBA データソース (外部API)]
```

### 学習・利用の中心とするAgentCoreの構成要素

- **Runtime**: エージェントコードをホスティング・実行する基盤。本プロジェクトの中核。
- **Memory**: 短期記憶(直近の会話コンテキスト)と長期記憶(ユーザーの嗜好・要約など)を管理し、対話の文脈維持に利用する。

Identity / Code Interpreter / Browser / Observability などの他のAgentCore構成要素は、必要に応じて後から検討する(現時点では優先度低)。

### NBAデータソースについて

データ取得元のAPIは未確定(検討中)。候補としては balldontlie.io(無料枠あり、APIキー認証、選手・チーム・試合データを取得可能)などがあるが、採用は未決定。実装に着手する際は、認証方式・レート制限・取得可能なデータ種別を確認した上で選定すること。

## 技術スタック方針

- **バックエンド**: Python(AgentCore上で動作するエージェントロジック、外部API連携を実装)
- **フロントエンド**: React(後回し。バックエンド・AgentCoreの動作確認を優先してから着手)
- `.gitignore` には IntelliJ / React / Python / Terraform のテンプレートが含まれており、インフラ構築にTerraformを使う可能性も視野にある(未確定)

## 開発の進め方

1. まずは設計・方針の言語化を優先し、実装は急がない
2. 実装に入る際は、AgentCore Runtime上でエージェントを動かすところから着手し、CLIまたはAPIレベルで動作確認する
3. 動作確認ができてから、Memoryによる会話履歴管理を順次組み込む
4. フロントエンド(React)はバックエンドの動作確認後に着手する

## 作業上の注意

- ビルド/lint/テストの仕組みはまだ存在しない。コマンドを推測せず、実装段階で実際の設定ファイル(`pyproject.toml`、`package.json` など)を確認すること
- AWS Bedrock AgentCore は2025年にGA(一般提供)となった比較的新しいサービスのため、実装時はAWS公式ドキュメント(https://docs.aws.amazon.com/bedrock-agentcore/)で最新のAPI・SDK仕様を確認すること
- アーキテクチャ・採用技術が確定し次第、本ファイルを更新して実態と乖離しないようにする