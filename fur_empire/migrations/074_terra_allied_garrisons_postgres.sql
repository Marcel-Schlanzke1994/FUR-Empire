CREATE TABLE terra_allied_garrison_policies (
  home_colony_id TEXT PRIMARY KEY REFERENCES colonies(colony_id) ON DELETE RESTRICT,
  host_user_id TEXT NOT NULL REFERENCES users(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  capacity INTEGER NOT NULL DEFAULT 300 CHECK(capacity BETWEEN 1 AND 300),
  rule_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  updated BIGINT NOT NULL
);
CREATE TABLE terra_allied_garrisons (
  id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL REFERENCES world(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  host_user_id TEXT NOT NULL REFERENCES users(id),
  host_colony_id TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE RESTRICT,
  contributor_id TEXT NOT NULL REFERENCES users(id),
  source_colony_id TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE RESTRICT,
  army TEXT NOT NULL,
  tactics INTEGER NOT NULL CHECK(tactics>=0),
  rule_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  status TEXT NOT NULL CHECK(status IN ('travelling','active')),
  created BIGINT NOT NULL,
  CHECK(host_user_id<>contributor_id)
);
CREATE INDEX terra_allied_garrison_host ON terra_allied_garrisons(host_colony_id,status,id);
CREATE INDEX terra_allied_garrison_contributor ON terra_allied_garrisons(contributor_id,status,id);
INSERT INTO schema_versions(version) VALUES (74);
