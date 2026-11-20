CREATE TABLE season_awards(
  season_id TEXT NOT NULL REFERENCES seasons(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  award TEXT NOT NULL CHECK(award IN ('season_champion','goal_achieved')),
  score BIGINT NOT NULL CHECK(score>=0),
  created BIGINT NOT NULL,
  PRIMARY KEY(season_id,user_id,award)
);
CREATE INDEX season_awards_user ON season_awards(user_id,created DESC,season_id);
CREATE TRIGGER season_awards_no_update BEFORE UPDATE ON season_awards
  BEGIN SELECT RAISE(ABORT,'season awards are immutable'); END;
CREATE TRIGGER season_awards_no_delete BEFORE DELETE ON season_awards
  BEGIN SELECT RAISE(ABORT,'season awards are immutable'); END;
