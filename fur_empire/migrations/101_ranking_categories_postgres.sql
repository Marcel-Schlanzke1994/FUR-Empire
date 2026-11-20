CREATE TABLE season_ranking_snapshots(
  season_id TEXT PRIMARY KEY REFERENCES seasons(id),
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  closed_at BIGINT NOT NULL
);
CREATE TABLE season_ranking_standings(
  season_id TEXT NOT NULL REFERENCES season_ranking_snapshots(season_id),
  category TEXT NOT NULL CHECK(category IN ('overall','economy','research','pve','war','regions')),
  user_id TEXT NOT NULL REFERENCES users(id),
  display_name TEXT NOT NULL,
  score BIGINT NOT NULL CHECK(score>=0),
  rank INTEGER NOT NULL CHECK(rank>0),
  PRIMARY KEY(season_id,category,user_id),
  UNIQUE(season_id,category,rank)
);
CREATE INDEX season_ranking_category_page
  ON season_ranking_standings(season_id,category,rank);
CREATE OR REPLACE FUNCTION reject_season_ranking_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'season ranking snapshots are immutable'; END; $$;
CREATE TRIGGER season_ranking_snapshots_no_update_delete BEFORE UPDATE OR DELETE ON season_ranking_snapshots
  FOR EACH ROW EXECUTE FUNCTION reject_season_ranking_mutation();
CREATE OR REPLACE FUNCTION reject_season_category_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'season ranking standings are immutable'; END; $$;
CREATE TRIGGER season_ranking_standings_no_update_delete BEFORE UPDATE OR DELETE ON season_ranking_standings
  FOR EACH ROW EXECUTE FUNCTION reject_season_category_mutation();
INSERT INTO schema_versions(version) VALUES (101) ON CONFLICT(version) DO NOTHING;
