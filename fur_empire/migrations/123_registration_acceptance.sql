BEGIN;
CREATE TABLE IF NOT EXISTS registration_acceptance (
 user_id TEXT PRIMARY KEY REFERENCES users(id),
 terms_version TEXT NOT NULL,
 privacy_version TEXT NOT NULL,
 accepted_at BIGINT NOT NULL,
 language TEXT NOT NULL CHECK(language IN ('de','en','es','fr'))
);
INSERT INTO schema_versions(version) VALUES (123) ON CONFLICT(version) DO NOTHING;
COMMIT;
