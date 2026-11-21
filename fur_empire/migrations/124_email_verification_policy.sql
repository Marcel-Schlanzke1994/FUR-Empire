BEGIN;
CREATE TABLE IF NOT EXISTS email_verification_pending (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    created BIGINT NOT NULL
);
INSERT INTO schema_versions(version) VALUES (124) ON CONFLICT(version) DO NOTHING;
COMMIT;
