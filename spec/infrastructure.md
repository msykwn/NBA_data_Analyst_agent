# NBA データアナリストエージェント インフラ設計書

本書は `spec/architecture.md`(アーキテクチャ設計書)を踏まえた、AWSインフラの構築方針を定義する。
アプリケーション側(エージェント実装)の設計判断は `spec/architecture.md` および `spec/features/` 配下の個別要件ファイルを参照。本書はAWSリソースの構築・運用に関わる方針を扱う。

## 1. 前提

- AWSアカウントは既に保有している(本書時点でアカウント内にAWSリソースは何もない、まっさらな状態)
- 本プロジェクトは AWS Bedrock AgentCore の学習を主目的とした個人学習用途であり、本番運用は想定しない
- ビルド/lint/テストの仕組みと同様、インフラのCI/CDパイプラインも本書時点では存在しない

## 2. リージョン・環境構成

### 2.1 リージョン: ap-northeast-1(東京)

**ap-northeast-1** を使用する。

- **検討事項**: AgentCoreは2025年GAの新しいサービスのため、利用可能リージョンが限定される懸念があった
- **確認結果**: AWS公式ドキュメント([Supported AWS Regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html))より、ap-northeast-1 では AgentCore Runtime / Memory / Gateway / Identity / Built-in Tools / Observability / Policy / Evaluations がサポート対象であることを確認した(プレビュー機能の一部 `harness` `payments` のみ東京は未対応だが、本プロジェクトでは利用しない)
- Amazon Bedrock(Claude呼び出し)も東京リージョンのリージョナルエンドポイントで利用可能であることを確認済み
- **方針**: AgentCore Runtime/Memory + Bedrock(Claude)を含め、**東京リージョン単体で完結する構成**とする。リージョンを跨ぐ必要はない

### 2.2 環境構成: 単一環境

dev/prod のような環境分離は行わず、**単一のAWSアカウント・単一環境**でリソースを構築する。

- **理由**: 学習目的のプロジェクトであり、環境分離による運用の複雑化よりも、シンプルにAgentCore・AWSリソースの構築自体に集中できることを優先する
- 環境分離が必要になった場合は、将来の検討事項として改めて設計する(11節)

## 3. ネットワーク構成(VPC)

**自前のVPCは作成しない**方針とする。

- **理由**: AgentCore Runtimeはマネージド環境(AWS管理のネットワーク)で実行されるため、自前VPCを用意する必然性が低い。VPC関連の設計・運用コストを排除し、学習対象であるAgentCore自体の理解にリソースを割く
- 外部NBA API呼び出しやBedrock呼び出しも、マネージド環境からインターネット経由・AWS内部経路で完結する想定
- VPC内での実行が必要な要件(セキュリティ要件など)が明確になった場合は、将来の検討事項として改めて検討する(11節)

## 4. Terraformによるインフラ管理

`spec/architecture.md` 8節の方針に基づき、Terraformでインフラを管理する。本書ではその具体的な構成を定義する。

### 4.1 コード配置場所: リポジトリ直下に `terraform/`

Terraformコードは、アプリケーションコードと同じリポジトリの直下 `terraform/` ディレクトリに配置する。

- **検討した選択肢**:
  - (A) リポジトリ直下に `terraform/` を配置し、アプリケーションコードと一元管理する
  - (B) インフラコードを別リポジトリに分離する
- **採用方針と理由**: (A) を採用。小規模な学習用プロジェクトであり、変更サイクルもアプリケーションコードと密接に関わる(例: AgentCore Runtimeの実行ロール権限を機能追加に合わせて調整する、など)ため、別リポジトリに分けるのは過剰。`.gitignore` に既にTerraformテンプレート関連の記載があり、この構成と整合する

### 4.2 State管理: S3 + DynamoDBによるリモート管理

Terraformのstateは、**S3バケット(state本体の保存)+ DynamoDBテーブル(state lockingによる排他制御)** によるリモートバックエンドで管理する。

- **検討した選択肢**:
  - (A) S3 + DynamoDBによるリモートstate管理
  - (B) ローカルstate(`terraform.tfstate` を `.gitignore` で除外し、ローカルのみで保持)
- **採用方針と理由**: (A) を採用。AWSでのTerraform運用における定番構成であり、学習として実践しておく価値が高い。将来的に複数環境・複数人運用に発展した場合にも見直しが不要になる
- **既知のブートストラップ問題と対応方針**: state管理用のS3バケット・DynamoDBテーブル自体をTerraformで管理しようとすると「stateを置く場所がまだ存在しない」という鶏卵問題が生じる。これらのリソースは、Terraform管理外(AWS CLIまたはマネジメントコンソールでの手動作成、あるいは `local` backendで一度だけapplyしてから `s3` backendへ移行する等)で先に用意し、以降のリソースをS3 backend経由で管理する方針とする。具体的な手順は実装時に決定する

### 4.3 エージェントコードのデプロイ: ローカルから手動実行

AgentCore Runtimeへのエージェントコード自体のデプロイは、`spec/architecture.md` 8節の方針通りTerraformの管理範囲外とし、**開発者のローカル環境からAgentCore CLI/SDK(例: `agentcore launch`)を手動実行する**方式とする。

- **検討した選択肢**:
  - (A) ローカルから手動実行
  - (B) GitHub Actions等のCI/CD経由で自動デプロイ
- **採用方針と理由**: (A) を採用。学習フェーズでは、デプロイ手順自体を手元で確認しながら理解することを優先する。CI/CD化(B)は、手動デプロイのフローが固まった後の発展的な検討事項として位置づける(11節)

## 5. IAM権限設計

IAMロール・ユーザーは、**必要最小限の権限で設計**する方針とする。

- **理由**: 学習目的のプロジェクトであっても、最小権限の原則(Principle of Least Privilege)はAWS運用における基本的なベストプラクティスであり、実践しておく価値が高い。`AdministratorAccess` 等の広範な権限で開始すると、後から絞り込む機会が失われやすい
- **対象となるロール・ユーザー**:
  - **AgentCore Runtime 実行ロール**: Bedrock(Claude)呼び出し、Secrets Manager参照、AgentCore Memory操作、CloudWatch Logsへの出力など、エージェントの動作に必要な権限のみを付与する
  - **Terraform実行ユーザー/ロール**: インフラ構築・変更に必要なリソース(IAM、AgentCore Memory、Secrets Manager、S3、DynamoDB、Budgets等)の管理権限を付与する。個人学習用途のため、開発者個人のIAMユーザーに必要な権限をアタッチする運用を想定する
- 各ロールの具体的なポリシー(許可するアクション・リソースの範囲)は、実装段階で必要な操作を洗い出しながら設計する

## 6. 認証情報管理(Secrets Manager)

`spec/architecture.md` 7節の方針に基づき、外部NBA APIキー等の認証情報はAWS Secrets Managerで管理する。本書ではインフラ観点での補足を記載する。

- Secrets Manager自体のリソース定義(シークレット名、ローテーション設定の要否など)はTerraformで管理する
- シークレットの**値**(実際のAPIキー)はTerraformコードに直接記述せず、`.gitignore` で除外される `*.tfvars` 等を経由して投入する、またはAWS CLI/コンソールで個別に設定する方針とする(リポジトリへの認証情報混入を防ぐため)
- 具体的な投入・運用方法は実装段階で決定する

## 7. コスト管理

学習目的のプロジェクトにおいて意図せぬ高額請求を早期検知するため、**AWS Budgets による予算アラート**を設定する。

- **方針**: 月額予算を設定し、実績または予測が一定割合(例: 50%, 80%, 100%)を超えた際にメール通知を受け取る
- **理由**: 設定コストが低く、最小限の仕組みで意図しない高額請求のリスクを早期に検知できる。学習用途では使った分だけ課金されるサービス(Bedrock、AgentCore等)を中心に使うため、想定外の使用量増加に気づける仕組みがあると安心して試行錯誤できる
- 予算額・通知しきい値・通知先メールアドレスなどの具体的な設定値は実装段階で決定する
- AWS Budgets自体のリソース定義はTerraformで管理する

## 8. ログ・観測性(Observability)

`spec/architecture.md` 10節の方針(AgentCore Runtimeが標準で出力するCloudWatch Logsを活用)を踏襲する。インフラ観点では、CloudWatch Logsのロググループ・保持期間などの設定が必要になった場合にTerraformで管理する。

具体的なロググループ名・保持期間・アラーム設定などは実装段階で検討する。

## 9. デプロイフロー全体像

本書の方針を踏まえた、インフラ構築・アプリケーションデプロイの全体的な流れは以下の通り。

1. **ブートストラップ**(手動・1回限り): Terraform state管理用のS3バケット・DynamoDBテーブルを作成する(4.2節)
2. **インフラ構築**(Terraform): IAMロール、AgentCore Memory、Secrets Manager、Budgets等のAWSリソースを `terraform apply` で構築する
3. **エージェントコードのデプロイ**(AgentCore CLI/SDK): ローカル環境から `agentcore launch` 等を手動実行し、AgentCore Runtimeにエージェントコードをデプロイする(4.3節)
4. **動作確認**: REST API経由でエージェントの動作を確認する(`spec/architecture.md` 9節と対応)

## 10. 状態

採用。本書の方針に基づき、実装段階でTerraformコード・IAMポリシー等の詳細を詰めていく。

実装過程で生じた判断・変更は、本書または関連する個別要件ファイルに都度追記していく。

## 11. 今後の検討事項

- 環境分離(dev/prod等)の導入(2.2節で見送り)
- VPC内でのAgentCore Runtime実行(3節で見送り)
- エージェントコードデプロイのCI/CD化(4.3節で見送り)
- Terraformでのエージェントコードデプロイの一元管理化(`spec/architecture.md` 11節と対応)
- ロギング・監視の強化(ロググループ設計、アラーム設定など。8節)