# GRAFIK.md — FUR EMPIRE Vollständiger Grafik-Produktionsplan

> Diese Datei in das ROOT des echten FUR-Workspaces als `GRAFIK.md` übernehmen und während der Codex-Implementierung pflegen. Jeder benötigte Asset erhält einen eindeutigen Datensatz. Dateigrößen sind **Designvorgaben für NEU zu erzeugende FUR-Assets**, keine Behauptung vorhandener Dateien.

## 1. Design-DNA

**Setting:** Eigenständiges Cyber-FUR-Strategiespiel mit Terra-Sektoren, technisch-militärischer Zivilisation und Orbit. **Look:** dunkles Navy/Anthrazit, metallische Goldakzente, gedämpftes Cyan für Karteninformationen, präzise taktische Hierarchie, wenig dekorativer visueller Lärm. Hohe Lesbarkeit bei Dunkel- und Hellmodus; Text auf kontrastreichen, ruhigen Panels. Keine Übernahmen von OGame-, Tribal-Wars- oder anderen Drittanbieter-Assets ohne dokumentierte Rechte.

Beispielpalette: Hintergrund `#0B111A`, Surface `#162432`, sekundäres Panel `#213444`, Gold `#D4AD66`, helles Gold `#F2D59D`, Cyan `#5ED3DF`, Erfolg `#47B38F`, Gefahr `#E87876`. Farbkontrast nach WCAG AA prüfen, sobald die Gesamttestphase beginnt. Diese Palette ist ein Ausgangsentwurf und darf designkonsistent verbessert werden.

## 2. Startkatalog mit Größen und Produktionsregeln

| Asset-ID / Familie | Zielgröße | Format | Transparenz | Detaillierte Vorgabe / Verwendung |
|---|---:|---|---|---|
| FUR-LOGO-PRIMARY | 2048 × 2048 | PNG + SVG | ja | Eigenständiges FUR-Kaninchen-/Imperiums-Emblem, metallisches Gold/Cyber, ohne fremde Marken; Login, Navigation, Community |
| FUR-LOGO-WIDE | 2400 × 720 | PNG + SVG | ja | Wortmarke FUR EMPIRE, volle und kompakte Variante |
| FUR-FAVICON | 512 × 512 | PNG + SVG | ja | Stark vereinfachtes, auch 16 px lesbares Emblem |
| FUR-HERO-TERRA | 2560 × 1440 | WebP/AVIF | nein | Cinematischer Cyber-FUR-Stützpunkt in dramatischer Landschaft, freie Textzone für Login |
| FUR-HERO-ORBIT | 2560 × 1440 | WebP/AVIF | nein | Originale Raumschiffe und Mondbasis, dunkle Stimmung, ohne OGame-Replik |
| FUR-CARD-EVENT | 1920 × 640 | WebP/AVIF | nein | Wiederverwendbare Event- und Saison-Banner mit freier Textzone |
| FUR-SOCIAL-PREVIEW | 1200 × 630 | PNG/WebP | nein | Vorschaubild für das eigene Spiel, Logo/Artwork lesbar |
| TERRA-TERRAIN-ATLAS | 1024 × 1024 | PNG/WebP + JSON | ja | Nahtloser Tile-Atlas für Wald, Ebenen, Berge, Pässe, Wasser, Sonderfelder; Tile-Grundfläche 128 × 128; Kantenübergänge konsistent |
| TERRA-FOG-STATES | 256 × 256 je Zustand | PNG/SVG | ja | unbekannt / gesehen-veraltet / aktuell; Informationsgeheimnis auch im Backend wahren |
| TERRA-MAP-MARKERS | 128 × 128 je Icon | SVG/PNG | ja | eigene/fremde Kolonie, neutral, Boss, Allianz, Transport, Angriff, Spionage, Schatz, Warnung, Favorit |
| TERRA-BUILDING-* | 1024 × 1024 je Gebäude | WebP/PNG | ja | Alle Basis-, Produktions-, Verteidigungs- und Spezialgebäude, Winkel/Perspektive über Set konsistent; Stufenvarianten als Overlay/Markierung |
| TERRA-UNIT-* | 768 × 768 je Einheit | WebP/PNG | ja | Bestehende Ranger/Wächter/Sturmmech plus neue Spezialtruppen, vollständige Silhouette, Front-3/4-Ansicht, keine Beschriftung im Bild |
| TERRA-DEFENSE-* | 768 × 768 | WebP/PNG | ja | Schildwall, Geschütztürme, Befestigungen, Spezialverteidigung |
| TECH-ICON-* | 256 × 256 | SVG/PNG | ja | Jeder Knoten im Forschungsbaum, konsistente Kategorienfarben; je Icon Alt-Text |
| RESOURCE-ICON-* | 128 × 128 | SVG/PNG | ja | Holz/Stein/Erz/Energie/Daten und alle weiteren von Regeln geforderten Güter |
| ITEM-ICON-* | 256 × 256 | WebP/PNG | ja | Jede Inventar-/Crafting-Kategorie inklusive Seltenheitsrahmen getrennt |
| HERO-PORTRAIT-* | 768 × 1024 | WebP/PNG | nein | Originale FUR-Fraktionshelden, konsistente Portraitkomposition |
| NPC-PORTRAIT-* | 768 × 1024 | WebP/PNG | nein | Neutrale Fraktionen, Kommandeure, Bossfiguren, eigene IP |
| QUEST-ILLUSTRATION-* | 1200 × 675 | WebP/AVIF | nein | Questkapitel und Kampagnenabschnitte, kein Text im Bild |
| ALLIANCE-BADGE-* | 512 × 512 | SVG/PNG | ja | Originale Embleme/standardisierte Badge-Teile, gut erkennbar im Listenmodus |
| ORBIT-SPACE-BACKGROUND-* | 3840 × 2160 | WebP/AVIF | nein | Sternfelder, Nebel, Raumbereiche als atmosphärische Kartenebene, nicht als OGame-Kopie |
| ORBIT-PLANET-* | 1024 × 1024 | WebP/PNG | ja | Planetentypen, Monde, Asteroiden, Ressourcenobjekte |
| ORBIT-SHIP-* | 1024 × 1024 je Klasse | WebP/PNG | ja | Alle 14 Schiffe aus dem tatsächlichen Regelkatalog; einheitliche 3/4-Perspektive, großzügige Silhouettenfreiheit |
| ORBIT-STATION-* | 1024 × 1024 | WebP/PNG | ja | Raumstationen, Verteidigung, Sprungtor, Sensorrelais |
| FX-COMBAT-* | 1024 × 1024 Sheet | WebP/PNG+JSON | ja | Effekte/Schilde/Explosionen mit explizitem Frame-Layout, reduzierte Bewegung möglich |
| UI-ICON-SET | 24 × 24 ViewBox | SVG | ja | Navigation, Status, Timer, Handel, Logistik, Berichte, Zugänglichkeit |
| UI-EMPTY-STATES | 640 × 360 | SVG/WebP | wahlweise | Keine Einheiten / keine Kolonien / keine Missionen / noch keine Nachricht usw. |
| UI-LOADING-INDICATORS | 128 × 128 | SVG/CSS | ja | Ladezustände ohne flackernde Animation, prefers-reduced-motion berücksichtigen |
| UI-PANEL-TEXTURES | 512 × 512 | WebP | ja | Ruhiges, wiederholbares Cyber-Panel-Muster, extrem niedriger Kontrast |

**Responsive:** 1× und 2× Varianten für Rasterillustrationen; bei Hero-Bildern zusätzlich 1600×900 und 960×1280 Crop. Nutze `srcset` und Lazy Loading, damit UI unter mobilen Netzen nutzbar bleibt. SVGs bevorzugen, wenn sie semantisch und performant geeignet sind.

## 3. Datensatz je Asset (pflichtig)

```yaml
asset_id: ORBIT-SHIP-[REGEL-ID]
feature_ids: ["ORBIT-..."]
screens: ["Orbit-Flottenwerft", "Orbit-Flotte", "Kampfbericht"]
path: static/assets/orbit/ships/[regel-id].webp
status: planned # planned | generating | integrated | asset_pending | final
exact_size_px: [1024, 1024]
format: webp
transparent: true
variants: ["default", "damaged", "selected"]
alt_de: "Eigenständiges Raumschiff der Klasse ..."
source_creator: "FUR Original / verwendetes Tool"
license: "owned-original / dokumentierte Erlaubnis"
creative_brief: "Eigenständiges Cyber-FUR-Militärschiff ..."
generation_prompt: "..."
negative_constraints: ["keine Fremdmarken", "kein Text", "kein Wasserzeichen", "kein OGame-Nachbau"]
fallback: static/assets/fallbacks/orbit-ship.svg
ui_binding: "konkreter Komponentenpfad und Asset-Referenz"
acceptance: "im echten Spiel an allen zugeordneten Stellen sichtbar, keine Broken Links"
```

## 4. Arbeitsauftrag für Codex

1. Inventarisiere tatsächliche Screens, Feature-IDs und vorhandene Originalassets.
2. Lege **für jede neue Bau-/Tech-/Unit-/Orbit-/NPC-/Quest-/Saisonklasse** einen eigenen Assetdatensatz an, der exakt auf die Regel-ID referenziert. Die Tabelle oben ist nur die verpflichtende Familienübersicht, nicht die vollständige Anzahl.
3. Erzeuge sofort SVG/CSS-Assets, die du rechtssicher selbst erstellen kannst. Verwende verfügbare Bildgenerierung für die restlichen Originalmotive; erzeuge keine bloßen Links auf nicht vorhandene Bilder.
4. Wenn Bildgenerierung nicht verfügbar: dokumentiere präzisen Prompt, Maße, Perspektive, Transparenz, Stil, Varianten, Dateinamen und Backend-/UI-Verwendung und nutze ein funktionierendes eigenes Fallback.
5. Trage Rechte, Urheber und Lizenznachweis in Asset Manifest / `THIRD_PARTY_NOTICES.md` ein.
6. Binde die Assets in echte UI-Komponenten ein. Keine ungefüllten Karten, verwaisten Dateien oder Bildverweise auf Referenz-Repositories.
7. Erst in der abschließenden globalen Testphase Asset-Existenz, Bildabmessungen, Copyright-Verzeichnis, Mobile Crop, Kontrast und Fallback per Prüfskript validieren.


## Konkrete Integration 2026-11-09 — ungetestet

Alle zehn folgenden Original-SVGs sind in der Warenbörse gebunden. Exakte Metadaten und Produktionsprompts: `assets/ASSET_MANIFEST.json`. Die übrigen Familien oben bleiben `asset_pending`; das Gesamtinventar ist noch offen.

| Asset | Datei | Maße | Format | Transparenz | Status |
|---|---|---|---|---|---|
| RESOURCE-WOOD | static/assets/goods/wood.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-STONE | static/assets/goods/stone.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-ORE | static/assets/goods/ore.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-ALLOY | static/assets/goods/alloy.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-CIRCUITS | static/assets/goods/circuits.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-TEXTILES | static/assets/goods/textiles.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-RATIONS | static/assets/goods/rations.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-MEDICINE | static/assets/goods/medicine.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-LUBRICANT | static/assets/goods/lubricant.svg | 128 × 128 | SVG | ja | integrated_unverified |
| RESOURCE-CERAMICS | static/assets/goods/ceramics.svg | 128 × 128 | SVG | ja | integrated_unverified |
