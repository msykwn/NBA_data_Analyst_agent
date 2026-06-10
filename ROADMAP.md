# ロードマップ

> 作業の都度このファイルを参照し、完了したフェーズはチェックを入れて更新すること。

## フェーズ1: AgentCore Runtime デプロイ 🔄 進行中
- [ ] AgentCore Runtime にエージェントをデプロイ
- [ ] REST API エンドポイント経由での動作確認
- 別セッションで `spec/features/agentcore-deployment.md` をもとに準備中

## フェーズ2: フロントエンド(React)
- [ ] チャットUI の実装
- [ ] AgentCore Runtime(REST API)との接続

## フェーズ3: Memory(短期記憶)の組み込み
- [ ] AgentCore Memory と orchestrator を接続
- [ ] `session_id` ベースの会話コンテキスト維持
- [ ] 「さっきの選手と比較して」のような指示語が解決できることを確認

## フェーズ4: 品質・安定性の強化
- [ ] エラーハンドリングの整備（API障害時のユーザーへの返し方など）
- [ ] ログ出力の整備（CloudWatch Logs 活用）
- [ ] 期間表現解釈の精度検証・必要なら日付計算ツール化（ADR に保留として記録済み）

## 将来フェーズ(優先度低)
- AgentCore Gateway 経由の MCP 化
- 長期記憶によるパーソナライズ
