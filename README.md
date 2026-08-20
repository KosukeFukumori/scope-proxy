# scope-proxy

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

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

本番ビルド (`npm run build`) の成果物は `backend/app/main.py` から `/_admin/` 配下で配信されます。

## 環境変数 (backend/.env)

`backend/.env.example` を参照してください。

## セキュリティ上の注意

- 未マッチのpath/methodへのリクエストはデフォルトで拒否されます(404)。
- 新規追加されたオペレーションはデフォルトで無権限です(allowlist)。
- 削除されたオペレーションは論理削除(`is_active=false`)され、常に拒否されます。

## ライセンス

[MIT](./LICENSE)
