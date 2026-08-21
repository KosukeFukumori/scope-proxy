# scope-proxy

[English](./README.md)

認証機能を持たない既存APIサーバー(OpenAPI JSONを公開)の手前に立ち、トークンベースの認可とプロキシ機能を提供するラッパーサーバーです。

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

### バックエンド

```bash
cd backend
uv sync
uv run scripts/create_admin_user.py  # 初回管理ユーザー作成
uv run uvicorn app.main:app --reload
```

DBスキーマのマイグレーションは起動時に自動実行されます(詳細は下記の[DBマイグレーション](#dbマイグレーション)を参照)。

### フロントエンド

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

## 環境変数 (backend/.env)

`backend/.env.example` を参照してください。

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

## ライセンス

[MIT](./LICENSE)
