CREATE TABLE IF NOT EXISTS alliance_military_score_ledger(
  mission_id TEXT NOT NULL,
  user_id TEXT NOT NULL REFERENCES users(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  category TEXT NOT NULL CHECK(category IN ('attack','defense','support')),
  points INTEGER NOT NULL CHECK(points>0),
  rules_version TEXT NOT NULL,
  created BIGINT NOT NULL,
  PRIMARY KEY(mission_id,user_id,category)
);
CREATE INDEX alliance_military_season_score
  ON alliance_military_score_ledger(world_id,created,alliance_id,user_id);
CREATE TABLE IF NOT EXISTS season_alliance_snapshots(
  season_id TEXT PRIMARY KEY REFERENCES seasons(id),
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  closed_at BIGINT NOT NULL,
  eligibility_policy TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS season_alliance_standings(
  season_id TEXT NOT NULL REFERENCES season_alliance_snapshots(season_id),
  alliance_id TEXT NOT NULL,
  alliance_name TEXT NOT NULL,
  alliance_tag TEXT NOT NULL,
  score BIGINT NOT NULL CHECK(score>=0),
  rank INTEGER NOT NULL CHECK(rank>0),
  eligible_accounts INTEGER NOT NULL CHECK(eligible_accounts>=0),
  PRIMARY KEY(season_id,alliance_id),
  UNIQUE(season_id,rank)
);
CREATE TRIGGER alliance_military_score_no_update BEFORE UPDATE ON alliance_military_score_ledger
  BEGIN SELECT RAISE(ABORT,'alliance military score is immutable'); END;
CREATE TRIGGER alliance_military_score_no_delete BEFORE DELETE ON alliance_military_score_ledger
  BEGIN SELECT RAISE(ABORT,'alliance military score is immutable'); END;
CREATE TRIGGER season_alliance_snapshots_no_update BEFORE UPDATE ON season_alliance_snapshots
  BEGIN SELECT RAISE(ABORT,'season alliance snapshots are immutable'); END;
CREATE TRIGGER season_alliance_snapshots_no_delete BEFORE DELETE ON season_alliance_snapshots
  BEGIN SELECT RAISE(ABORT,'season alliance snapshots are immutable'); END;
CREATE TRIGGER season_alliance_standings_no_update BEFORE UPDATE ON season_alliance_standings
  BEGIN SELECT RAISE(ABORT,'season alliance standings are immutable'); END;
CREATE TRIGGER season_alliance_standings_no_delete BEFORE DELETE ON season_alliance_standings
  BEGIN SELECT RAISE(ABORT,'season alliance standings are immutable'); END;
INSERT INTO schema_versions(version) VALUES (86) ON CONFLICT(version) DO NOTHING;
