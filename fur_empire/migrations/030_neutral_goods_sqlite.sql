BEGIN IMMEDIATE;
CREATE TABLE neutral_goods_trades (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL REFERENCES users(id),
    world_id INTEGER NOT NULL REFERENCES world(id),
    colony_id TEXT NOT NULL,
    command_token TEXT NOT NULL,
    created BIGINT NOT NULL,
    details TEXT NOT NULL,
    UNIQUE(owner, command_token)
);
CREATE INDEX neutral_goods_trades_owner ON neutral_goods_trades(owner, world_id, created, id);
CREATE TRIGGER neutral_goods_trades_no_update BEFORE UPDATE ON neutral_goods_trades
BEGIN SELECT RAISE(ABORT, 'immutable neutral goods trade'); END;
CREATE TRIGGER neutral_goods_trades_no_delete BEFORE DELETE ON neutral_goods_trades
BEGIN SELECT RAISE(ABORT, 'immutable neutral goods trade'); END;
INSERT INTO schema_versions(version) VALUES (30) ON CONFLICT(version) DO NOTHING;
COMMIT;
