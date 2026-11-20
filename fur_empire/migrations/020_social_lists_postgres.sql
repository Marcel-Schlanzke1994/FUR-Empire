CREATE TABLE friendships(
  a TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  b TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  requested_by TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK(status IN ('pending','accepted')),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  PRIMARY KEY(a,b),
  CHECK(a < b),
  CHECK(requested_by=a OR requested_by=b)
);
CREATE INDEX friendships_recipient ON friendships(b,status,updated DESC);
CREATE INDEX friendships_requester ON friendships(requested_by,status,updated DESC);
CREATE TABLE player_blocks(
  blocker TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  blocked TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created BIGINT NOT NULL,
  PRIMARY KEY(blocker,blocked),
  CHECK(blocker<>blocked)
);
CREATE INDEX player_blocks_target ON player_blocks(blocked,blocker);
INSERT INTO schema_versions(version) VALUES (20) ON CONFLICT(version) DO NOTHING;
