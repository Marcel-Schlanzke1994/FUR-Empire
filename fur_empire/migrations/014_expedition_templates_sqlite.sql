BEGIN IMMEDIATE;
CREATE TABLE mission_templates_v14(
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 32),
    mode TEXT NOT NULL CHECK(mode IN ('attack','scout','transport','station','expedition')),
    army TEXT NOT NULL,
    capture INTEGER NOT NULL DEFAULT 0 CHECK(capture IN (0,1)),
    created BIGINT NOT NULL
);
INSERT INTO mission_templates_v14(id,owner,name,mode,army,capture,created)
SELECT id,owner,name,mode,army,capture,created FROM mission_templates;
DROP TABLE mission_templates;
ALTER TABLE mission_templates_v14 RENAME TO mission_templates;
CREATE UNIQUE INDEX mission_templates_name ON mission_templates(owner, lower(name));
CREATE INDEX mission_templates_order ON mission_templates(owner, created, id);
INSERT INTO schema_versions(version) VALUES (14) ON CONFLICT(version) DO NOTHING;
COMMIT;
