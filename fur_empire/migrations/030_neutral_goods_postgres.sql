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
CREATE FUNCTION reject_neutral_goods_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable neutral goods trade'; END;
$$;
CREATE TRIGGER neutral_goods_trades_immutable BEFORE UPDATE OR DELETE ON neutral_goods_trades
FOR EACH ROW EXECUTE FUNCTION reject_neutral_goods_change();
