CREATE TABLE account_ban_appeals(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reason TEXT NOT NULL CHECK(length(reason) BETWEEN 3 AND 1000),
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','resolved')),
  resolution TEXT CHECK(resolution IN ('deny_ban_appeal','grant_ban_appeal')),
  created BIGINT NOT NULL,
  resolved BIGINT,
  resolver_id TEXT REFERENCES users(id) ON DELETE SET NULL,
  CHECK((status='open' AND resolution IS NULL AND resolved IS NULL AND resolver_id IS NULL)
     OR (status='resolved' AND resolution IS NOT NULL AND resolved IS NOT NULL AND resolver_id IS NOT NULL))
);
CREATE UNIQUE INDEX account_ban_appeal_open_idx
  ON account_ban_appeals(user_id) WHERE status='open';
CREATE INDEX account_ban_appeals_queue_idx
  ON account_ban_appeals(status,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (106) ON CONFLICT(version) DO NOTHING;
