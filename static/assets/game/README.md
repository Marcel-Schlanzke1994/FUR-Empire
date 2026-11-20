# FUR EMPIRE game art

This directory is the runtime copy of the approved Terra and Orbit art packages supplied in `FUR_EMPIRE_ASSETS/`. The source delivery and its archives remain unchanged.

## Runtime catalog

`asset-catalog.json` indexes all 302 catalogued motifs: 169 Terra and 133 Orbit. Its file lists cover 512 optimized SVG, PNG, and WebP exports. Every catalog URL resolves under FastAPI's `/static` mount. Use the shared `assetUrl()` / `assetImage()` helpers in `static/app.js` for dynamic UI. Catalog keys are package and category qualified, such as `terra/buildings/hq` and `orbit/ships/probe`; aliases are provided only where an ID is unambiguous. The catalog helper prefers WebP, then SVG, then the first supplied export.

## Connected views

- Terra title art, FUR wordmark and favicon brand the login and game shell.
- Terra navigation and resource symbols identify the primary interface and economy.
- Terra terrain, fog, and location markers render the surveyed world map.
- Terra buildings, research, units, campaign directives, and inventory items use their matching illustrations where the game data exposes a matching catalog key.
- Orbit title, ship, orbital-object, and planet art illustrate the orbit system and colony panels.
- Remaining approved variants, transitions, effects, faction marks, decorative components, and alternate states remain addressable through the runtime catalog for feature-specific rendering.

The original delivery's QA reports and license/provenance records are kept in `FUR_EMPIRE_ASSETS/`; this runtime copy does not replace or modify those records.
