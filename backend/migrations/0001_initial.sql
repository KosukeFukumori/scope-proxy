-- 初期スキーマ: 全テーブルを CREATE TABLE IF NOT EXISTS で定義（べき等）
-- SQLModel.metadata.create_all() が生成していたスキーマと同一の内容にしている

CREATE TABLE IF NOT EXISTS backend_config (
    id INTEGER NOT NULL,
    endpoint_url VARCHAR NOT NULL,
    openapi_url VARCHAR NOT NULL,
    last_fetched_at DATETIME,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS operations (
    operation_id VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    summary VARCHAR,
    is_active BOOLEAN NOT NULL,
    PRIMARY KEY (operation_id)
);

CREATE TABLE IF NOT EXISTS schema_snapshots (
    id INTEGER NOT NULL,
    fetched_at DATETIME NOT NULL,
    spec_hash VARCHAR NOT NULL,
    diff_summary VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL,
    email VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    token_hash VARCHAR NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME,
    revoked_at DATETIME,
    last_used_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_tokens_token_hash ON tokens (token_hash);

CREATE TABLE IF NOT EXISTS token_permissions (
    id INTEGER NOT NULL,
    token_id INTEGER NOT NULL,
    operation_id VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(token_id) REFERENCES tokens (id),
    FOREIGN KEY(operation_id) REFERENCES operations (operation_id)
);

CREATE INDEX IF NOT EXISTS ix_token_permissions_operation_id ON token_permissions (operation_id);
CREATE INDEX IF NOT EXISTS ix_token_permissions_token_id ON token_permissions (token_id);
