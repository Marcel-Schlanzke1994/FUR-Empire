CREATE TABLE commander_heroes(
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  world_id INTEGER NOT NULL REFERENCES world_settings(world_id) ON DELETE CASCADE,
  experience INTEGER NOT NULL DEFAULT 0 CHECK(experience>=0),
  military INTEGER NOT NULL DEFAULT 0 CHECK(military BETWEEN 0 AND 10),
  economy INTEGER NOT NULL DEFAULT 0 CHECK(economy BETWEEN 0 AND 10),
  recon INTEGER NOT NULL DEFAULT 0 CHECK(recon BETWEEN 0 AND 10),
  command INTEGER NOT NULL DEFAULT 0 CHECK(command BETWEEN 0 AND 10),
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  PRIMARY KEY(user_id,world_id)
);
CREATE TABLE commander_hero_xp_events(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  world_id INTEGER NOT NULL,
  source_job_id TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  experience INTEGER NOT NULL CHECK(experience>0),
  rules_version TEXT NOT NULL,
  rules_hash TEXT NOT NULL CHECK(length(rules_hash)=64),
  created INTEGER NOT NULL,
  UNIQUE(user_id,world_id,source_job_id),
  FOREIGN KEY(user_id,world_id) REFERENCES commander_heroes(user_id,world_id) ON DELETE CASCADE
);
CREATE TRIGGER commander_hero_xp_no_update BEFORE UPDATE ON commander_hero_xp_events BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER commander_hero_xp_no_delete BEFORE DELETE ON commander_hero_xp_events BEGIN SELECT RAISE(ABORT, 'immutable'); END;
INSERT INTO schema_versions(version) VALUES (94);
