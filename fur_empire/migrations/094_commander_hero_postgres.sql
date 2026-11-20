CREATE TABLE commander_heroes(
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  world_id BIGINT NOT NULL REFERENCES world_settings(world_id) ON DELETE CASCADE,
  experience BIGINT NOT NULL DEFAULT 0 CHECK(experience>=0),
  military SMALLINT NOT NULL DEFAULT 0 CHECK(military BETWEEN 0 AND 10),
  economy SMALLINT NOT NULL DEFAULT 0 CHECK(economy BETWEEN 0 AND 10),
  recon SMALLINT NOT NULL DEFAULT 0 CHECK(recon BETWEEN 0 AND 10),
  command SMALLINT NOT NULL DEFAULT 0 CHECK(command BETWEEN 0 AND 10),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  PRIMARY KEY(user_id,world_id)
);
CREATE TABLE commander_hero_xp_events(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  world_id BIGINT NOT NULL,
  source_job_id TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  experience BIGINT NOT NULL CHECK(experience>0),
  rules_version TEXT NOT NULL,
  rules_hash CHAR(64) NOT NULL CHECK(length(rules_hash)=64),
  created BIGINT NOT NULL,
  UNIQUE(user_id,world_id,source_job_id),
  FOREIGN KEY(user_id,world_id) REFERENCES commander_heroes(user_id,world_id) ON DELETE CASCADE
);
CREATE FUNCTION reject_commander_hero_xp_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable'; END;
$$;
CREATE TRIGGER commander_hero_xp_no_update BEFORE UPDATE ON commander_hero_xp_events
FOR EACH ROW EXECUTE FUNCTION reject_commander_hero_xp_mutation();
CREATE TRIGGER commander_hero_xp_no_delete BEFORE DELETE ON commander_hero_xp_events
FOR EACH ROW EXECUTE FUNCTION reject_commander_hero_xp_mutation();
INSERT INTO schema_versions(version) VALUES (94) ON CONFLICT(version) DO NOTHING;
