-- Switch operations.operation_id from the raw OpenAPI operationId to a
-- sha256 hash of (method, path, operationId), and keep the original
-- operationId in a new display-only column.
--
-- Existing rows cannot be re-hashed in SQLite (no sha256 function), so the
-- operations and token_permissions tables are cleared instead: the admin
-- re-syncs the schema and re-grants token permissions after upgrading.
-- This is the fail-safe direction for a permission proxy.

DELETE FROM token_permissions;
DELETE FROM operations;

ALTER TABLE operations ADD COLUMN openapi_operation_id VARCHAR;
