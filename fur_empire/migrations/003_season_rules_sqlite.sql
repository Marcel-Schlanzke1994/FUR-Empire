CREATE TRIGGER IF NOT EXISTS season_rules_no_update
BEFORE UPDATE ON season_rules
BEGIN
    SELECT RAISE(ABORT, 'season rules are immutable');
END;
CREATE TRIGGER IF NOT EXISTS season_rules_no_delete
BEFORE DELETE ON season_rules
BEGIN
    SELECT RAISE(ABORT, 'season rules are immutable');
END;
