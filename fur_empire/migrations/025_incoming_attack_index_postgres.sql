CREATE TABLE IF NOT EXISTS incoming_attack_index(
  job_id TEXT PRIMARY KEY,
  target_user TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_colony_id TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE CASCADE,
  due BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS incoming_attack_index_target_due
  ON incoming_attack_index(target_user,due,job_id);
