# scope-proxy

[English](./README.md)

[![CI](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](./backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/frontend-React%2019-61DAFB.svg)](./frontend/package.json)

認証機能を持たない既存APIサーバー(OpenAPI JSONを公開)の手前に立ち、トークンベースの認可とプロキシ機能を提供するラッパーサーバーです。

**認可サーバー不要、OAuthのやり取り不要、接続先APIへのコード変更も不要。** OpenAPIスキーマを指定するだけで、接続先の各オペレーションに対しトークンごとに付与・剥奪できる権限が自動的に用意されます。認証を持たない社内APIを、数分でアクセス制御されたAPIに変えられます。

## なぜ scope-proxy か

- **接続先APIの変更が一切不要** — 接続先は認可の存在を意識する必要がありません。scope-proxyが手前に立ち、まったく同じURL構造で応答します。
- **OAuthサーバーの構築が不要** — トークンはセルフサービスで発行される不透明な文字列で、接続先自身のOpenAPIスキーマから取得した `operationId` 単位でスコープされます。クライアント登録もリダイレクトURIも、IdPも不要です。
- **スキーマの変化を安全に扱う** — 接続先のOpenAPIが変化すると、新規オペレーションは無権限(allowlist)から始まるため、意図せず公開されることがありません。
- **フットプリントが小さい** — FastAPI 1サービス + SQLiteのみで構成され、`docker compose up` でコンテナ1つとしてデプロイできます。

## 特徴

- 自前のセルフサービス方式によるトークンベース認可(OAuth三者間フローではない)
- トークンごとに、接続先OpenAPIの `operationId` 単位で権限(許可するエンドポイント)を設定
- 認可されたリクエストのみ接続先サーバーへ、**元のURL構造を維持したまま**転送するプロキシ機能
- 接続先OpenAPIスキーマの変化を検知し、安全側(allowlist)に倒す形で権限に反映
- ログイン後、ユーザー自身がトークンを発行・管理できるフロントエンド

## アーキテクチャ概要

- ラッパーサーバーのルート `/` 以下は、接続先バックエンドと**完全に同一のURL構造**でプロキシされます(例: バックエンドの `GET /users/1` は `GET /users/1` としてそのまま転送)。
- 管理系API・管理画面はすべて `/_admin/*` に予約されています。接続先のOpenAPIに `/_admin` で始まるオペレーションがある場合は、スキーマ同期時に警告のうえプロキシ対象から除外されます。
- トークンはランダムな不透明文字列で発行され、DBにはSHA-256ハッシュのみが保存されます。生の値は発行時に一度しか表示されません。

## セットアップ

### Docker Compose(お手軽に試す場合)

ポートを1つにまとめたい場合、フロントエンドをビルドしてbackendイメージに同梱し、Docker Composeで起動できます。

```bash
docker compose up --build
```

これで管理画面とプロキシの両方が `http://localhost:8000` の1ポートで動作します。SQLiteのDBファイルは `scope_proxy_db` という名前付きボリュームに永続化されます。初回管理ユーザーの作成は次のコマンドで行います。

```bash
docker compose exec app .venv/bin/python scripts/create_admin_user.py
```

本番運用では `docker-compose.yml` 内で `SECRET_KEY` を固定値に設定してください。未設定の場合は再起動のたびにランダム生成され、セッションが毎回無効になります。

### 開発実行

#### バックエンド

```bash
cd backend
uv sync
uv run scripts/create_admin_user.py  # 初回管理ユーザー作成
uv run uvicorn app.main:app --reload
```

DBスキーマのマイグレーションは起動時に自動実行されます(詳細は下記の[DBマイグレーション](#dbマイグレーション)を参照)。

#### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

管理画面は OS のカラースキーム設定に追従し、ライト/ダークの両方に対応しています。

開発時、フロントエンドの `/_admin/api/*` へのリクエストは `vite.config.ts` の設定によりバックエンド(`http://127.0.0.1:8000`)へプロキシされます。バックエンドを先に起動してから `npm run dev` を実行してください。

本番ビルド (`npm run build`) の成果物は `backend/app/main.py` から `/_admin/` 配下で配信されます(SPAのため、実ファイルが存在しないパスは `index.html` にフォールバックします)。

## DBマイグレーション

`backend/migrations/` には連番の冪等なSQLファイル(`0001_initial.sql`, `0002_xxx.sql`, ...)を置きます。起動のたびに(`app.main.lifespan` → `app.db.init_db`)、`app.migration_runner.run_migrations` が `schema_migrations` テーブルに未記録のファイルをファイル名順に適用します。手動で実行するマイグレーションコマンドは無く、`backend/migrations/` に新しい連番の `.sql` ファイルを追加するだけで、次回アプリ起動時に自動適用されます。

## ヘルスチェック

`GET /_admin/api/health` は認証不要のエンドポイントで、アプリが起動しDBに接続できている状態であれば `{"status": "ok"}` を返します。キャッチオールのプロキシルーターより前に登録されているため、認証の対象外です。Docker Compose の `healthcheck` やロードバランサーの死活監視に利用してください(`docker-compose.yml` と `Dockerfile` の `HEALTHCHECK` を参照)。

## 環境変数 (backend/.env)

`backend/.env.example` を参照してください。

CORSは既定で無効です(`CORS_ALLOWED_ORIGINS` が空)。これは安全側の既定値で、ブラウザのCORSプリフライト `OPTIONS` を含む全リクエストが通常の認証フローに乗り、Bearerトークンなしでは拒否されます。つまり、ブラウザ上のSPAなどからプロキシを直接呼び出すことは**できません**。それを許可するには、`CORS_ALLOWED_ORIGINS` に許可するオリジンをカンマ区切りで設定してください。設定したオリジンからのプリフライトリクエストは、認証・ルーティングに到達する前に応答されるようになります。

## テスト

```bash
cd backend
uv run pytest
uv run ruff check .
```

```bash
cd frontend
npm run lint
npm run build
```

## セキュリティ上の注意

- 未マッチのpath/methodへのリクエストはデフォルトで拒否されます(404)。
- 新規追加されたオペレーションはデフォルトで無権限です(allowlist)。
- 削除されたオペレーションは論理削除(`is_active=false`)され、常に拒否されます。
- CORSは既定で無効です。`CORS_ALLOWED_ORIGINS` で有効化しても、影響するのはプリフライト `OPTIONS` のハンドシェイクのみで、実際のリクエストには引き続き有効なBearerトークンが必要です。

## ライセンス

[MIT](./LICENSE)
