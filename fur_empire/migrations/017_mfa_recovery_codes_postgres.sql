CREATE TABLE IF NOT EXISTS mfa_recovery_codes(
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    created BIGINT NOT NULL,
    PRIMARY KEY(user_id,code_hash)
);
CREATE INDEX IF NOT EXISTS mfa_recovery_codes_user_created
    ON mfa_recovery_codes(user_id,created);
INSERT INTO schema_versions(version) VALUES (17) ON CONFLICT(version) DO NOTHING;
