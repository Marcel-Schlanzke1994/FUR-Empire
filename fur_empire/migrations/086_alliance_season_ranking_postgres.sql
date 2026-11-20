CREATE TABLE IF NOT EXISTS alliance_military_score_ledger(
  mission_id TEXT NOT NULL,
  user_id TEXT NOT NULL REFERENCES users(id),
  world_id BIGINT NOT NULL REFERENCES world(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  category TEXT NOT NULL CHECK(category IN ('attack','defense','support')),
  points INTEGER NOT NULL CHECK(points>0),
  rules_version TEXT NOT NULL,
  created BIGINT NOT NULL,
  PRIMARY KEY(mission_id,user_id,category)
);
CREATE INDEX IF NOT EXISTS alliance_military_season_score
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
CREATE OR REPLACE FUNCTION reject_alliance_season_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'alliance season evidence is immutable'; END; $$;
CREATE TRIGGER alliance_military_score_no_update BEFORE UPDATE OR DELETE ON alliance_military_score_ledger
  FOR EACH ROW EXECUTE FUNCTION reject_alliance_season_mutation();
CREATE TRIGGER season_alliance_snapshots_no_update BEFORE UPDATE OR DELETE ON season_alliance_snapshots
  FOR EACH ROW EXECUTE FUNCTION reject_alliance_season_mutation();
CREATE TRIGGER season_alliance_standings_no_update BEFORE UPDATE OR DELETE ON season_alliance_standings
  FOR EACH ROW EXECUTE FUNCTION reject_alliance_season_mutation();
INSERT INTO schema_versions(version) VALUES (86) ON CONFLICT(version) DO NOTHING;
