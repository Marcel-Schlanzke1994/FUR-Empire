ALTER TABLE colonies ADD COLUMN name_key TEXT NOT NULL DEFAULT '';
CREATE INDEX colonies_name_key ON colonies(name_key);
