# 深夜のテック Bar - 要件定義書 v3.0.0

## 1. システム概要

### 1.1 目的

- 技術者が気軽に立ち寄れる「バー」という仮想空間の提供
- Vector Search 技術を活用した自然な会話の展開
- AI バーテンダーによる適切な会話の進行
- 匿名性を重視した居心地の良い空間作り

### 1.2 基本方針

- Vertex Gemini API を活用した自然な対話の実現
- PostgreSQL の Vector Search 機能による関連会話の検索
- シンプルなアーキテクチャと実装の容易性重視
- セッションベースの軽量な管理システム
- バックエンドの Fastapi とフロントエンドの Vue を単一コンテナでホスティング

## 2. システム機能

### 2.1 基本機能

1. セッション管理

   - 自動生成される Guest_XXX フォーマットのユーザー名
   - セッション ID のみによる匿名の利用者管理
   - 15 分の無活動で自動退店
   - 在店中のみ閲覧可能な会話履歴

2. バーテンダー（AI エージェント）

   - 状況に応じた会話介入の制御
   - 複数人会話時の適切な距離感維持
   - Vector Search を活用した過去の会話の自然な引用
   - メッセージは常にユーザーメッセージの後に時系列で表示

3. 空間管理
   - WebSocket によるリアルタイムな在店者管理
   - 店内の雰囲気に応じた会話調整

### 2.2 会話システム

1. バーテンダーの介入制御

   - 一人客：積極的な対話
   - 複数客：状況に応じた介入（必要に応じて静観）
   - 沈黙時：適度な話題提供

2. 会話履歴の管理
   - WebSocket によるリアルタイムな会話の共有
   - Vector Search による関連会話の検索と自然な引用
   - クライアント側でタイムスタンプ＋メッセージタイプによるソート

### 2.3 プロンプト設計

```python
def construct_prompt(current_message: str, display_name: str, context: dict) -> str:
    prompt = f"""
    あなたは「深夜のテックバー」のベテランバーテンダー（マスター）として振る舞ってください。
    技術者たちが仕事帰りに立ち寄る、アットホームな雰囲気のバーです。

    現在の状況:
    - 店内のお客様: {', '.join(f'{user}さん' for user in context['current_users'])}
    - 店内の雰囲気: {'quiet' if len(context['current_users']) <= 2 else 'lively'}
    - 発言したお客様: {display_name}さん

    以下の方針で接客してください:
    1. フレンドリーな口調で、でも礼儀正しく
    2. 他のお客様がいる場合は、全体の会話の流れを意識
    3. 技術の話題については詳しく、でも堅苦しくならないように
    4. 簡潔に返答
    5. 過去の会話に関連する内容があれば、自然な形で会話に織り交ぜる
    6. 盛り上がっていたり、口を出すべきでないと判断したら ... のみを返答

    直近の会話:
    {chr(10).join(context['recent_messages'])}

    {context.get('similar_context', '')}

    新しいメッセージ:
    {display_name}さん: {current_message}
    """

    logger.debug(f"Generated prompt: {prompt}")
    return prompt
```

## 3. データベース設計

### 3.1 テーブル構造

PostgreSQL を使用し、以下のテーブル構造を採用します：

```sql
-- 拡張機能を確認（既に存在する場合はスキップ）
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- セッションテーブル
CREATE TABLE tech_bar_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_key VARCHAR(64) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    embedding vector(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    combined_content TEXT,
    UNIQUE (session_key, display_name)
);

-- 会話テーブル
CREATE TABLE tech_bar_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES tech_bar_sessions(id),
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- メッセージテーブル
CREATE TABLE tech_bar_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES tech_bar_conversations(id),
    content TEXT NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('user', 'system')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    sequence_num INTEGER NOT NULL,
    embedding vector(768),
    UNIQUE (conversation_id, sequence_num)
);

-- 関連メッセージテーブル
CREATE TABLE tech_bar_related_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_message_id UUID NOT NULL REFERENCES tech_bar_messages(id),
    related_message_id UUID NOT NULL REFERENCES tech_bar_messages(id),
    similarity_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tech_bar_relation UNIQUE (source_message_id, related_message_id)
);

-- インデックスの作成
CREATE INDEX idx_tech_bar_messages_conversation_id
ON tech_bar_messages(conversation_id);

CREATE INDEX idx_tech_bar_conversations_session_id
ON tech_bar_conversations(session_id);

CREATE INDEX idx_tech_bar_sessions_session_key
ON tech_bar_sessions(session_key);

CREATE INDEX idx_tech_bar_sessions_active
ON tech_bar_sessions(is_active)
WHERE is_active = true;

CREATE INDEX idx_tech_bar_sessions_embedding
ON tech_bar_sessions
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_tech_bar_messages_embedding
ON tech_bar_messages
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- セッション検索用の複合インデックス
CREATE INDEX idx_tech_bar_sessions_composite
ON tech_bar_sessions(session_key, display_name, is_active);
```

#### Embedding に関する注意点

- Gemini API の text-embedding-004 モデルを使用
- エンベディングは既に正規化されているため、追加の正規化は不要
- 768 次元のベクトルとして保存

#### データベース監視用クエリ

```sql
-- メッセージとembeddingの基本情報確認(仮)
SELECT
    id,
    content,
    type,
    created_at,
    embedding IS NULL as is_embedding_null,
    CASE
        WHEN embedding IS NOT NULL THEN vec_dim(embedding)
        ELSE 0
    END as embedding_dimension
FROM messages
ORDER BY created_at DESC
LIMIT 5;

-- embeddingの有無によるメッセージ数の集計(仮)
SELECT
    type,
    COUNT(*) as total_messages,
    COUNT(embedding) as messages_with_embedding,
    COUNT(*) - COUNT(embedding) as messages_without_embedding
FROM messages
GROUP BY type;

-- embeddingの正規化チェック(仮)
SELECT
    id,
    content,
    type,
    created_at,
    sqrt(l2_squared_norm) as l2_norm,
    CASE
        WHEN abs(sqrt(l2_squared_norm) - 1.0) > 0.01 THEN 'Not Normalized'
        ELSE 'OK'
    END as normalization_status
FROM (
    SELECT
        id,
        content,
        type,
        created_at,
        embedding <-> embedding as l2_squared_norm
    FROM messages
    WHERE embedding IS NOT NULL
) subquery
WHERE abs(sqrt(l2_squared_norm) - 1.0) > 0.01
OR l2_squared_norm IS NULL
LIMIT 10;
```

#### デバッグコマンド

```bash
# データベースへの接続
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db

# テーブル一覧の確認
\dt

# テーブル構造の確認
\d messages
\d conversations
\d chat_sessions

# メッセージ数の確認
SELECT type, COUNT(*) FROM messages GROUP BY type;

# 最新のメッセージを確認
SELECT id, content, type, created_at
FROM messages
ORDER BY created_at DESC
LIMIT 5;
```

### 3.2 主要な機能と特徴

1. セッション管理

   - UUID ベースの一意なセッション識別
   - 表示名によるユーザー区別
   - メタデータによる追加情報の柔軟な保存

2. 会話管理

   - セッションごとの会話グループ化
   - タイトル付けとアーカイブ機能
   - タイムスタンプによる履歴追跡

3. メッセージ処理

   - ユーザー/システムメッセージの区別
   - シーケンス番号による順序管理
   - スレッド構造のサポート
   - 豊富なメタデータ（トークン数、モデル情報など）

4. ベクトル検索

   - pg_vector 拡張による効率的な類似度検索
   - 768 次元のベクトル保存（Gemini API 互換）
   - IVF フラットインデックスによる高速検索

5. 関連メッセージ管理

   - メッセージ間の類似度スコアの記録
   - 重複関係の防止
   - 時系列での関連性追跡

6. WebSocket ベースのリアルタイム接続管理

## 4. チャットシステム実装

### 4.1 基本構造

vue-advanced-chat を使用して Vuetify で実装中。シングルルームモード、カスタムダークテーマスタイリング、WebSocket 更新、メッセージステータス管理を含む。

### 4.2 ストリーミング実装

```python
// filepath: backend/src/functions/main_chainlit.py
// ...existing code...

# Geminiからの応答をストリーミング
msg = cl.Message(content="", author="システム")
await msg.send()

collected_response = ""
async for response in client.aio.models.generate_content_stream(
    model="gemini-2.0-flash-exp",
    contents=full_prompt
):
    if response.text:
        collected_response += response.text
        await msg.stream_token(response.text)

await msg.update()
```

## 5. 会話フロー

### 5.1 入店時（新規セッション開始）

1. ユーザーがバーに入店（アクセス）
2. システムが自動的にセッション ID を生成
3. バックエンドで以下の処理を実行:

- 新規セッションを作成
- 現在の店内状況を確認（他の客の有無）
- Gemini API でバーテンダーの応答を生成（「いらっしゃいませ」など）
- セッション情報を保存

### 5.2 バーでの会話（セッション継続時）

1. メッセージ送信時:

- セッション ID で発言者を識別
- 店内の状況を確認（客数、会話の活性度）
- Vector Search で関連する過去の会話を検索
- バーテンダーの介入判断（複数客の場合は必要に応じて静観）
- Gemini API で適切な応答を生成（介入が不要な場合は"..."）
- ストリーミングで応答を表示

### 5.3 退店時（セッション終了）

1. 自動退店（15 分間の無活動時）:

- 最終アクティビティから 15 分経過を検知
- セッションの終了処理
- 会話履歴のクリア

2. 通常退店（ブラウザを閉じる等）:

- セッションの終了処理
- 会話履歴のクリア

## 6. デプロイ方法

### 6.1 前提条件

- GCP プロジェクトの作成
- 必要な API の有効化:
  - Cloud SQL API
  - Cloud RUN API
- Cloud SQL Proxy のインストール

### 6.2 データベースセットアップ

1. ログインとプロジェクト設定

```bash
gcloud auth login --no-launch-browser
gcloud config set account your-account@example.com
gcloud config set project information-exchange-agent
```

2. Terraform の実行と CloudSQL インスタンスの作成

```bash
cd terraform/environments/dev
terraform init
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="db_password=your-password"
```

3. データベースとユーザーの作成

```bash
# データベースの作成
gcloud sql databases create vector_db --instance=vector-db-dev

# ユーザーの作成
gcloud sql users create vector_user \
    --instance=vector-db-dev \
    --password=your-password
```

4. Cloud SQL Proxy の起動

```bash
# プロキシの配置場所を確認
ls /workspace/cloud-sql-proxy

# プロキシの起動（別ターミナルで実行）
/workspace/cloud-sql-proxy "PROJECT_ID:REGION:INSTANCE_NAME" --port 5432
```

5. PostgreSQL クライアントのインストール

```bash
# Debian/Ubuntu系の場合
sudo apt-get update
sudo apt-get install postgresql-client

# または
# Alpine Linuxの場合
apk add postgresql-client
```

6. データベースへの接続とスキーマ設定

```bash
# 接続
PGPASSWORD=your-password psql -h localhost -p 5432 -U vector_user -d vector_db

# pg_vector拡張のインストール
CREATE EXTENSION IF NOT EXISTS vector;

# 以下のスキーマを実行
```

```sql
-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

[残りのスキーマ定義は同じため省略...]
```

7. Terraform の状態への追加（必要な場合）

```bash
# データベースの追加
terraform import module.cloudsql.google_sql_database.vector_database "projects/PROJECT_ID/instances/INSTANCE_NAME/databases/DATABASE_NAME"

# ユーザーの追加
terraform import module.cloudsql.google_sql_user.vector_db_user "projects/PROJECT_ID/instances/INSTANCE_NAME/users/USER_NAME"
```

### 6.3 アプリケーションデプロイ

1. 環境変数の設定

```bash
export PROJECT_ID=your-project-id
export REGION=asia-northeast1
export DB_INSTANCE=chat-db-dev
```

2. 必要なパッケージのインストール

```bash
pip install chainlit google-cloud-storage psycopg2-binary google-generativeai
```

3. Terraform の実行

```bash
cd terraform/environments/dev
terraform init
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION"
```

## 7. 開発環境セットアップ

1. 必要なツール

   - Python 3.11
   - PostgreSQL
   - Terraform
   - GCP SDK
   - Cloud SQL Proxy

2. ローカル開発用環境変数

```bash
# .env
GEMINI_API_KEY=your-api-key
DB_NAME=vector_db
DB_USER=vector_user
DB_PASSWORD=pass
DB_HOST=localhost
DB_PORT=5432
FUNCTIONS_EMULATOR=true
```

## 8. セキュリティに関する注意点

本システムは試験的な実装として、以下の点でセキュリティを簡略化しています：

- ユーザー認証なし（セッションキーのみで管理）
- データベース接続の暗号化最小限
- API 認証の省略
- 会話履歴の公開範囲制限なし

これらの機能は、本番環境への移行時に実装を検討する必要があります。

## 9. パフォーマンスに関する注意点

1. データベース最適化

   - インデックスの適切な設計
   - 会話履歴の取得時のページネーション検討
   - ベクトル検索のチューニング

2. スケーリング考慮事項
   - セッション数増加時の対応
   - 古いセッションのクリーンアップ
   - キャッシュ戦略の検討

## 10. 開発計画

1. フェーズ 1: 基本機能実装

   - セッション管理システム
   - 基本的な会話機能
   - バーテンダーの介入制御

2. フェーズ 2: 雰囲気作り

   - より自然な会話の流れ
   - バーテンダーの個性強化
   - 空間の演出改善

3. フェーズ 3: コミュニティ機能
   - 常連さん機能
   - 特別なイベントの開催
   - テーマナイトの実施

## 11. 制限事項

1. 技術的制限

   - PostgreSQL のベクトルインデックスサイズ制限
   - Gemini API のトークン制限
   - セッション管理の制限

2. 機能的制限

   - 同時接続数の制限
   - 会話履歴の保持期間
   - セッションの有効期限

3. セッション管理の制限
   - 同一表示名での同時アクセスの制限
   - セッション数の制限（パフォーマンスを考慮）
   - 非アクティブセッションの自動クリーンアップ

## 12. 運用管理

1. セッション管理(仮)

   ```sql
   -- アクティブセッション数の確認
   SELECT display_name, COUNT(*)
   FROM chat_sessions
   WHERE is_active = true
   GROUP BY display_name;

   -- 長期未使用セッションの非アクティブ化
   UPDATE chat_sessions
   SET is_active = false
   WHERE last_active_at < NOW() - INTERVAL '30 days';
   ```

## 13. データベース操作とデバッグ

### 13.1 Cloud SQL Proxy 設定

1. Cloud SQL Proxy の起動

```bash
# Cloud SQL Proxyを起動 (別ターミナルで実行)
./cloud-sql-proxy "information-exchange-agent:asia-northeast1:vector-db-dev" --port 5432
```

2. データベース接続確認

```bash
# 一般的な接続テスト
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -c "\dt"

# テーブル構造の確認
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -c "\d chat_sessions"
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -c "\d conversations"
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -c "\d messages"
```

### 13.2 会話履歴の確認

1. 基本的な会話履歴の確認

```bash
# 直近の会話履歴を取得
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -c "
SELECT
    m.sequence_num,
    m.type,
    m.content,
    m.created_at,
    cs.display_name
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
JOIN chat_sessions cs ON c.session_id = cs.id
ORDER BY m.created_at DESC
LIMIT 10;"
```

### 13.4 Embedding の生成と検証

1. エンベディング生成の確認

```python
from google import genai

# クライアントの初期化
client = genai.Client(api_key="your-api-key")  # ローカル環境の場合

# エンベディングの生成
response = client.models.embed_content(
    model="text-embedding-004",
    contents="テストメッセージ"
)

# 結果の確認
embedding = response.embeddings[0].values
print(f"Embedding dimension: {len(embedding)}")
```

2. データベースでのエンベディング検証(仮)

```sql
-- エンベディングの次元数確認
SELECT vec_dim(embedding) FROM messages WHERE embedding IS NOT NULL LIMIT 1;

-- コサイン類似度の確認
SELECT
    m1.content as text1,
    m2.content as text2,
    1 - (m1.embedding <=> m2.embedding) as cosine_similarity
FROM messages m1
CROSS JOIN messages m2
WHERE m1.id < m2.id
AND m1.embedding IS NOT NULL
AND m2.embedding IS NOT NULL
LIMIT 5;
```

## 14. ローカル開発環境

### 14.1 環境設定

1. 必要な環境変数

```bash
export FUNCTIONS_EMULATOR=true
export GEMINI_API_KEY=your-api-key-here
export DB_NAME=vector_db
export DB_USER=vector_user
export DB_PASSWORD=pass
export DB_HOST=localhost
export DB_PORT=5432
export PROJECT_ID=information-exchange-agent
```

2. アプリケーションの起動

```bash
cd backend/src/functions
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8083
```

### 14.2 デバッグ設定

1. VSCode launch.json の設定例

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8083"],
      "env": {
        "FUNCTIONS_EMULATOR": "true",
        "DB_HOST": "localhost"
      }
    }
  ]
}
```
