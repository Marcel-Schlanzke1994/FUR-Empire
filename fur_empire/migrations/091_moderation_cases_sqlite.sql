CREATE TABLE moderation_cases(
  id TEXT PRIMARY KEY,
  case_type TEXT NOT NULL CHECK(case_type IN ('message_report','mute_appeal')),
  reporter_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  target_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message_id TEXT REFERENCES messages(id) ON DELETE CASCADE,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','resolved')),
  resolution TEXT,
  created BIGINT NOT NULL,
  resolved BIGINT,
  resolver_id TEXT REFERENCES users(id) ON DELETE SET NULL,
  CHECK((case_type='message_report' AND message_id IS NOT NULL AND resolution IS NULL OR case_type='message_report' AND message_id IS NOT NULL AND resolution IS NOT NULL)
     OR (case_type='mute_appeal' AND message_id IS NULL))
);
CREATE UNIQUE INDEX moderation_case_report_once_idx
  ON moderation_cases(reporter_id,message_id) WHERE case_type='message_report';
CREATE UNIQUE INDEX moderation_case_open_appeal_idx
  ON moderation_cases(reporter_id) WHERE case_type='mute_appeal' AND status='open';
CREATE INDEX moderation_cases_queue_idx
  ON moderation_cases(status,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (91);
