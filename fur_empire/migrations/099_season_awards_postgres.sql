CREATE TABLE season_awards(
  season_id TEXT NOT NULL REFERENCES seasons(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  award TEXT NOT NULL CHECK(award IN ('season_champion','goal_achieved')),
  score BIGINT NOT NULL CHECK(score>=0),
  created BIGINT NOT NULL,
  PRIMARY KEY(season_id,user_id,award)
);
CREATE INDEX season_awards_user ON season_awards(user_id,created DESC,season_id);
CREATE OR REPLACE FUNCTION prevent_season_award_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'season awards are immutable'; END; $$;
CREATE TRIGGER season_awards_no_update_delete BEFORE UPDATE OR DELETE ON season_awards
FOR EACH ROW EXECUTE FUNCTION prevent_season_award_mutation();
