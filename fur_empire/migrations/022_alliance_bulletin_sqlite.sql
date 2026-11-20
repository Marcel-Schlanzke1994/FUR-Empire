CREATE TABLE alliance_bulletins(
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 80),
  body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1))
);
CREATE INDEX alliance_bulletins_feed ON alliance_bulletins(alliance_id,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (22) ON CONFLICT(version) DO NOTHING;
