CREATE OR REPLACE FUNCTION prevent_season_rules_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'season rules are immutable';
END;
$$;
DROP TRIGGER IF EXISTS season_rules_no_update ON season_rules;
CREATE TRIGGER season_rules_no_update
BEFORE UPDATE OR DELETE ON season_rules
FOR EACH ROW EXECUTE FUNCTION prevent_season_rules_mutation();
