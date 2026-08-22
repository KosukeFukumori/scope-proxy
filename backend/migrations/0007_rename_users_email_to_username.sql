-- Renames users.email to users.username as part of moving from email-based
-- login to username-based login. Existing values are carried over as-is.
ALTER TABLE users RENAME COLUMN email TO username;

DROP INDEX IF EXISTS ix_users_email;
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
