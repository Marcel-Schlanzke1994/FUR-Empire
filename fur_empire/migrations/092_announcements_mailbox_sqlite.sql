CREATE TABLE system_announcements(
  id TEXT PRIMARY KEY,
  world_id INTEGER REFERENCES world(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 80),
  body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
  created BIGINT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1))
);
CREATE INDEX system_announcements_scope_idx
  ON system_announcements(world_id,created DESC,id DESC);
CREATE TABLE system_mail(
  id TEXT PRIMARY KEY,
  recipient_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 80),
  body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
  created BIGINT NOT NULL,
  read_at BIGINT
);
CREATE INDEX system_mail_recipient_idx
  ON system_mail(recipient_id,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (92);
