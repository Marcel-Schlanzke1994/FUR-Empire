CREATE TABLE production_templates(
  id TEXT PRIMARY KEY,
  owner TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 32),
  kind TEXT NOT NULL CHECK(kind IN ('build','research','train')),
  item_key TEXT NOT NULL CHECK(length(item_key) BETWEEN 1 AND 100),
  count INTEGER NOT NULL CHECK(count BETWEEN 1 AND 100),
  created BIGINT NOT NULL
);
CREATE UNIQUE INDEX production_templates_name ON production_templates(owner, lower(name));
CREATE INDEX production_templates_order ON production_templates(owner, created, id);
INSERT INTO schema_versions(version) VALUES (19) ON CONFLICT(version) DO NOTHING;
