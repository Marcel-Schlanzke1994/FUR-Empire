BEGIN;
CREATE TABLE IF NOT EXISTS account_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    language TEXT NOT NULL CHECK(language IN ('de','en','es','fr'))
);
INSERT INTO schema_versions(version) VALUES (122) ON CONFLICT(version) DO NOTHING;
COMMIT;
