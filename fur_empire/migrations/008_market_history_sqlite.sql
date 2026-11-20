BEGIN IMMEDIATE;
CREATE TABLE market_trades(
    id TEXT PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES world(id),
    timestamp INTEGER NOT NULL,
    source_resource INTEGER NOT NULL CHECK(source_resource BETWEEN 0 AND 2),
    target_resource INTEGER NOT NULL CHECK(target_resource BETWEEN 0 AND 2),
    source_amount INTEGER NOT NULL CHECK(source_amount>0),
    target_amount INTEGER NOT NULL CHECK(target_amount>0),
    trade_kind TEXT NOT NULL CHECK(trade_kind IN ('neutral','player'))
);
CREATE INDEX market_trades_history ON market_trades(world_id,timestamp DESC,id);
CREATE TRIGGER market_trades_no_update BEFORE UPDATE ON market_trades BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER market_trades_no_delete BEFORE DELETE ON market_trades BEGIN SELECT RAISE(ABORT,'immutable'); END;
INSERT INTO schema_versions(version) VALUES (8) ON CONFLICT(version) DO NOTHING;
COMMIT;
