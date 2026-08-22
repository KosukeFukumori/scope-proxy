-- Tracks the outcome of the most recent schema sync attempt (manual or scheduled)
-- so the dashboard can show whether the last sync succeeded or failed.

ALTER TABLE backend_config ADD COLUMN last_sync_status VARCHAR;
ALTER TABLE backend_config ADD COLUMN last_sync_error VARCHAR;
