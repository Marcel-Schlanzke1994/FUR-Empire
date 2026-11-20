CREATE TABLE IF NOT EXISTS map_bookmarks(
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL,
    created BIGINT NOT NULL,
    PRIMARY KEY(user_id, target_id)
);
CREATE INDEX IF NOT EXISTS map_bookmarks_order ON map_bookmarks(user_id, created, target_id);
