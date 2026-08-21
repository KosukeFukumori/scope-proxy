-- Replace tokens.id's sequential autoincrement integer primary key with a
-- random UUID4 string, so token identifiers exposed via the API (and used
-- as URL path params) are not sequential/guessable.

ALTER TABLE tokens ADD COLUMN new_id VARCHAR;

UPDATE tokens
SET new_id = lower(
    hex(randomblob(4)) || '-' ||
    hex(randomblob(2)) || '-4' ||
    substr(hex(randomblob(2)), 2) || '-' ||
    substr('89ab', abs(random()) % 4 + 1, 1) ||
    substr(hex(randomblob(2)), 2) || '-' ||
    hex(randomblob(6))
);

ALTER TABLE token_permissions ADD COLUMN new_token_id VARCHAR;

UPDATE token_permissions
SET new_token_id = (SELECT new_id FROM tokens WHERE tokens.id = token_permissions.token_id);

CREATE TABLE IF NOT EXISTS tokens_v2 (
    id VARCHAR NOT NULL,
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

INSERT INTO tokens_v2 (id, user_id, name, token_hash, created_at, expires_at, revoked_at, last_used_at)
SELECT new_id, user_id, name, token_hash, created_at, expires_at, revoked_at, last_used_at FROM tokens;

CREATE TABLE IF NOT EXISTS token_permissions_v2 (
    id INTEGER NOT NULL,
    token_id VARCHAR NOT NULL,
    operation_id VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(token_id) REFERENCES tokens_v2 (id),
    FOREIGN KEY(operation_id) REFERENCES operations (operation_id)
);

INSERT INTO token_permissions_v2 (id, token_id, operation_id)
SELECT id, new_token_id, operation_id FROM token_permissions;

DROP TABLE token_permissions;
DROP TABLE tokens;

ALTER TABLE tokens_v2 RENAME TO tokens;
ALTER TABLE token_permissions_v2 RENAME TO token_permissions;

CREATE UNIQUE INDEX IF NOT EXISTS ix_tokens_token_hash ON tokens (token_hash);
CREATE INDEX IF NOT EXISTS ix_token_permissions_operation_id ON token_permissions (operation_id);
CREATE INDEX IF NOT EXISTS ix_token_permissions_token_id ON token_permissions (token_id);
