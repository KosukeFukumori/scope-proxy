# ![scope-proxy logo](./frontend/public/favicon.svg) scope-proxy

[English](./README.md)

[![CI](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](./backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/frontend-React%2019-61DAFB.svg)](./frontend/package.json)

認証機能を持たない既存APIサーバー(OpenAPI JSONを公開)の手前に立ち、トークンベースの認可とプロキシ機能を提供するラッパーサーバーです。

**認可サーバー不要、OAuthのやり取り不要、接続先APIへのコード変更も不要。** OpenAPIスキーマを指定するだけで、接続先の各オペレーションに対しトークンごとに付与・剥奪できる権限が自動的に用意されます。認証を持たない社内APIを、数分でアクセス制御されたAPIに変えられます。

## デモ

**[管理画面のデモを試す](https://kosukefukumori.github.io/scope-proxy/)** — ログイン: `admin` / `demo-password`

これは管理画面をGitHub Pages上にホストした静的ビルドで、すべてのAPI呼び出しはブラウザ内のモックデータで応答しています(`frontend/src/demo/mockApi.ts` 参照)。実際のバックエンドは存在せず、操作内容はブラウザタブを閉じると失われます。画面の見た目や操作感を確認するためのものです。scope-proxy自体を試す場合は、下記の[クイックスタート](#クイックスタートビルド済みイメージ)を使ってください。

## なぜ scope-proxy か

- **接続先APIの変更が一切不要** — 接続先は認可の存在を意識する必要がありません。scope-proxyが手前に立ち、まったく同じURL構造で応答します。
- **OAuthサーバーの構築が不要** — トークンはセルフサービスで発行される不透明な文字列で、接続先自身のOpenAPIスキーマから取得した `operationId` 単位でスコープされます。クライアント登録もリダイレクトURIも、IdPも不要です。
- **スキーマの変化を安全に扱う** — 接続先のOpenAPIが変化すると、新規オペレーションは無権限(allowlist)から始まるため、意図せず公開されることがありません。
- **フットプリントが小さい** — FastAPI 1サービス + SQLiteのみで構成され、`docker compose up` でコンテナ1つとしてデプロイできます。

## 特徴

- 自前のセルフサービス方式によるトークンベース認可(OAuth三者間フローではない)
- トークンごとに、接続先OpenAPIの `operationId` 単位で権限(許可するエンドポイント)を設定
- 認可されたリクエストのみ接続先サーバーへ、**元のURL構造を維持したまま**転送するプロキシ機能
- 接続先OpenAPIスキーマの変化を検知し、安全側(allowlist)に倒す形で権限に反映(ダッシュボードの「今すぐ更新」による手動実行に加え、`SCHEMA_SYNC_INTERVAL_SECONDS` によるバックグラウンドの定期自動同期にも対応)
- ログイン後、ユーザー自身がトークンを発行・管理できるフロントエンド

## アーキテクチャ概要

- ラッパーサーバーのルート `/` 以下は、接続先バックエンドと**完全に同一のURL構造**でプロキシされます(例: バックエンドの `GET /users/1` は `GET /users/1` としてそのまま転送)。
- 管理系API・管理画面はすべて `/_admin/*` に予約されています。接続先のOpenAPIに `/_admin` で始まるオペレーションがある場合は、スキーマ同期時に警告のうえプロキシ対象から除外されます。
- トークンはランダムな不透明文字列で発行され、DBにはSHA-256ハッシュのみが保存されます。生の値は発行時に一度しか表示されません。

## セットアップ

### クイックスタート(ビルド済みイメージ)

一番手早く試すには、GHCRで公開されているビルド済みイメージをpullしてそのまま実行します。このリポジトリをcloneする必要はありません。タグ付きリリースのたびに、`.github/workflows/docker-publish.yml` によってマルチアーキ(`linux/amd64`, `linux/arm64`)対応のイメージが公開されます。

```bash
docker pull ghcr.io/kosukefukumori/scope-proxy:latest

docker run -d --name scope-proxy \
  -p 8000:8000 \
  -v scope_proxy_db:/app/backend/data \
  -e DATABASE_URL=sqlite:////app/backend/data/scope_proxy.db \
  ghcr.io/kosukefukumori/scope-proxy:latest
```

これで管理画面とプロキシの両方が `http://localhost:8000` の1ポートで動作します。SQLiteのDBファイルは `scope_proxy_db` という名前付きボリュームに永続化されます。`http://localhost:8000/_admin/` を開いてください。まだアカウントが存在しない間は、その場で管理者のユーザー名とパスワードを設定するセットアップ画面が表示されます。

本番運用では、固定の `SECRET_KEY` も設定してください(`-e SECRET_KEY=...`)。未設定の場合は再起動のたびにランダム生成され、セッションが毎回無効になります。

### Docker Compose

このリポジトリをcloneしている場合、長い `docker run` コマンドの代わりに設定をファイルにまとめられるDocker Composeが便利です。`docker-compose.yml` は既定でローカルビルドを行いますが、GHCRのビルド済みイメージを使う場合は `build:` ブロックを `image: ghcr.io/kosukefukumori/scope-proxy:latest` に置き換えてください。

```bash
docker compose up --build
```

初回管理アカウントの作成方法は2通りあります。

- **画面から作成する**: `http://localhost:8000/_admin/` を開くだけです。まだアカウントが存在しない間は、その場で管理者のユーザー名とパスワードを設定するセットアップ画面が表示されます。
- **環境変数で作成する**(無人・スクリプト化されたデプロイ向け): `ADMIN_USERNAME` と `ADMIN_PASSWORD_HASH` の両方を(例えば `docker-compose.yml` の `app` サービスの環境変数として)設定します。起動時にアカウントが1つも存在しなければ、この設定から自動的にアカウントが作成されます。既にアカウントが存在する場合、これらの変数は無視されます。`ADMIN_PASSWORD_HASH` には平文パスワードではなく**bcryptハッシュ値**を設定する必要があります。ハッシュ値は次のコマンドで生成できます。

  ```bash
  docker compose exec app .venv/bin/python -c "import bcrypt, getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
  ```

  生成されたハッシュ値を `ADMIN_PASSWORD_HASH` に設定してください。

本番運用では `docker-compose.yml` 内で `SECRET_KEY` を固定値に設定してください。未設定の場合は再起動のたびにランダム生成され、セッションが毎回無効になります。

scope-proxyの管理アカウントは単一です。ログイン後は、管理画面の「アカウント」ページからユーザー名やパスワードを変更できます。`ADMIN_USERNAME`/`ADMIN_PASSWORD_HASH` とセットアップ画面は、この最初のアカウントを作成するためだけに使われます。

### 開発実行

#### バックエンド

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

DBスキーマのマイグレーションは起動時に自動実行されます(詳細は下記の[DBマイグレーション](#dbマイグレーション)を参照)。`http://127.0.0.1:8000/_admin/` を開き、セットアップ画面から初回管理アカウントを作成してください(あるいは事前に `ADMIN_USERNAME`/`ADMIN_PASSWORD_HASH` を設定しておくこともできます。[環境変数](#環境変数-backendenv)を参照)。

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

`ADMIN_USERNAME` と `ADMIN_PASSWORD_HASH` は初回管理アカウントを非対話で作成するための設定です。両方セットで指定する必要があり、まだアカウントが1つも存在しない場合にのみ有効になります。`ADMIN_PASSWORD_HASH` にはbcryptハッシュ値を設定してください。生成方法は次のとおりです。

```bash
cd backend
uv run python -c "import bcrypt, getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
```

未設定のままにしておくと、管理画面への初回アクセス時にセットアップ画面が表示され、そこから対話的にアカウントを作成できます。

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
