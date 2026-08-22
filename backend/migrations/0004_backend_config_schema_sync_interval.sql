-- Allows the schema sync interval to be overridden from the GUI at runtime.
-- NULL means "no override": the SCHEMA_SYNC_INTERVAL_SECONDS env var value is used instead.

ALTER TABLE backend_config ADD COLUMN schema_sync_interval_seconds INTEGER;
