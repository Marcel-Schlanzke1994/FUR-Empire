CREATE TABLE alliance_forum_threads(
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1))
);
CREATE INDEX alliance_forum_threads_feed
  ON alliance_forum_threads(alliance_id,created DESC,id DESC);
CREATE TABLE alliance_forum_posts(
  id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES alliance_forum_threads(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES users(id),
  body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 4000),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL
);
CREATE INDEX alliance_forum_posts_feed
  ON alliance_forum_posts(thread_id,created DESC,id DESC);
CREATE TABLE alliance_forum_reports(
  id TEXT PRIMARY KEY,
  post_id TEXT NOT NULL REFERENCES alliance_forum_posts(id) ON DELETE CASCADE,
  reporter_id TEXT NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL CHECK(length(reason) BETWEEN 1 AND 500),
  status TEXT NOT NULL CHECK(status IN ('pending','resolved')),
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  resolved_by TEXT REFERENCES users(id)
);
CREATE UNIQUE INDEX alliance_forum_one_pending_report
  ON alliance_forum_reports(post_id,reporter_id) WHERE status='pending';
CREATE INDEX alliance_forum_reports_review
  ON alliance_forum_reports(status,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (23) ON CONFLICT(version) DO NOTHING;
