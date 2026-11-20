CREATE TABLE alliance_shared_reports(
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  report_id TEXT NOT NULL,
  summary TEXT NOT NULL,
  created BIGINT NOT NULL,
  UNIQUE(owner_id,world_id,report_id)
);
CREATE INDEX alliance_shared_reports_scope_idx
  ON alliance_shared_reports(alliance_id,world_id,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (90) ON CONFLICT(version) DO NOTHING;
