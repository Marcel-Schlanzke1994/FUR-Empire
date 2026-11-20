ALTER TABLE mission_templates DROP CONSTRAINT mission_templates_mode_check;
ALTER TABLE mission_templates ADD CONSTRAINT mission_templates_mode_check
    CHECK(mode IN ('attack','scout','transport','station','expedition'));
INSERT INTO schema_versions(version) VALUES (14) ON CONFLICT(version) DO NOTHING;
