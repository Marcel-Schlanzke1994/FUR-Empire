CREATE TABLE IF NOT EXISTS season_rules(
    season_id TEXT PRIMARY KEY REFERENCES seasons(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    snapshot TEXT NOT NULL,
    digest TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('season_start','legacy_backfill'))
);
