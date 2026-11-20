CREATE TABLE IF NOT EXISTS alliance_transfer_requests(
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL UNIQUE REFERENCES alliances(id) ON DELETE CASCADE,
  leader_id TEXT NOT NULL REFERENCES users(id),
  successor_id TEXT NOT NULL REFERENCES users(id),
  created BIGINT NOT NULL,
  CHECK(leader_id<>successor_id)
);
CREATE INDEX IF NOT EXISTS alliance_transfer_successor
  ON alliance_transfer_requests(successor_id,alliance_id);
INSERT INTO schema_versions(version) VALUES (84) ON CONFLICT(version) DO NOTHING;
