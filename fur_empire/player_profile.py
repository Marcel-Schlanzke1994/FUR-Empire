"""Privacy-first, opt-in public player profiles."""

import hashlib
import json
from pathlib import Path

RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-player-profile-1.json").read_text(encoding="utf-8")
)
RULES_DIGEST = hashlib.sha256(
    json.dumps(RULES, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
TITLES: dict[str, str] = RULES["titles"]
BADGES: dict[str, str] = RULES["badges"]
MAX_BADGES = int(RULES["max_badges"])
