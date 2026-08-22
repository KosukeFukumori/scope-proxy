-- Adds request_logs: one row per proxied request (allowed or denied), so
-- token usage and denial rates can be inspected instead of only tracking
-- tokens.last_used_at.

CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER NOT NULL,
    token_id VARCHAR,
    operation_id VARCHAR,
    method VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    status INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(token_id) REFERENCES tokens (id),
    FOREIGN KEY(operation_id) REFERENCES operations (operation_id)
);

CREATE INDEX IF NOT EXISTS ix_request_logs_token_id ON request_logs (token_id);
CREATE INDEX IF NOT EXISTS ix_request_logs_operation_id ON request_logs (operation_id);
CREATE INDEX IF NOT EXISTS ix_request_logs_created_at ON request_logs (created_at);
