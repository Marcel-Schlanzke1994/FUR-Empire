CREATE TABLE player_notes(
  id TEXT PRIMARY KEY,
  owner TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  target_kind TEXT NOT NULL CHECK(target_kind IN ('sector','report')),
  sector_x INTEGER CHECK(sector_x BETWEEN 0 AND 63),
  sector_y INTEGER CHECK(sector_y BETWEEN 0 AND 63),
  report_id TEXT,
  body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 500),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  CHECK(
    (target_kind='sector' AND sector_x IS NOT NULL AND sector_y IS NOT NULL AND report_id IS NULL)
    OR
    (target_kind='report' AND sector_x IS NULL AND sector_y IS NULL AND report_id IS NOT NULL)
  )
);
CREATE UNIQUE INDEX player_notes_sector_target
  ON player_notes(owner,world_id,sector_x,sector_y) WHERE target_kind='sector';
CREATE UNIQUE INDEX player_notes_report_target
  ON player_notes(owner,world_id,report_id) WHERE target_kind='report';
CREATE INDEX player_notes_owner_world ON player_notes(owner,world_id,updated DESC);
INSERT INTO schema_versions(version) VALUES (21) ON CONFLICT(version) DO NOTHING;
