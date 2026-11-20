# FUR EMPIRE — VOLLSTÄNDIGES EIGENSTÄNDIGES GRAFIK-/UI-DESIGNSYSTEM

## 1. Identität
- Titel: **FUR EMPIRE**; optionaler Untertitel **Genesis of the Network**; originelle Cyber-Fantasy/Strategie statt Kopie von Die Stämme oder OGame.
- Kerntöne: Onyx `#0C1018`, dunkles Panel `#152635`, Gold `#C99A43`, Holografie-Cyan `#37B6C6`, Warnung `#E8B65B`, kritische Warnung `#D45F64`, helle Schrift `#F0F2F5`.
- Keine fremden Logos, OGame-Schiffsgrafiken, Tribal-Wars-Screenshots, geschützte UI-Skins oder als frei verfügbare Bilder behaupteten Assets. Eigene Herkunftsdaten als `assets/MANIFEST.json`.

## 2. Assetfamilien (alle erforderlich, eigene Erstellung)
- Corporate: Wordmark/Signet/Storymark, Favicon/Social-Square/OG Cover, Loading, Error, PWA-Icons.
- Terra: neun Terrain-Tile-Typen × Tag/Nacht × minimap/Map/large, Siedlungen in mind. fünf Entwicklungsstufen, Region-/Fog-/Frontlinien-Overlays, Fraktionsfarben, NPC-/Quest-/Eventmarker.
- Gebäude: FUR-2 acht Bestandsgebäude als eigene Illustrationen; neue 20 Gebäudetypen mit Icons und Isometrie/Detailansicht; Sperrstatus/Upgrade-Layer.
- Truppen: FUR-2 drei Basiseinheiten sowie zwölf neue Einheitentypen, zusätzlich sechs Fraktions-Spezialeinheiten; Icon, Portrait, Silhouette, animierbare Varianten optional.
- Krieg: Waffen-/Panzer-/Schild-/Status-Icons, Marschpfeile, Replay-Timeline, Erfolgs-/Verlust-Badges, Garnisonen, Artillerie, Spionage/Counterintel.
- Orbit: Galaxiekarten/Planeten, Monde/Stationen, Nebel-/Trümmer-/Warp-Effekte, 14 eigene Raumschiffklassen, Planeten-/Flottenstatus, UI-Badges.
- Sozial: drei Fraktionsembleme, Allianzbanner/Rank-Badges, Arena-, Saison-, Boss- und Achievement-Medaillen.
- Avatar/Community: eigene spielbare FUR-Rollen, Accountprofil, Hall of Fame; keine fotorealistischen fremden Charaktere oder markenrechtlich problematischen Vorlagen.

## 3. UI-Komponentenbibliothek
`GameShell`, `MainNav`, `MobileBottomNav`, `WorldSwitcher`, `ResourceBar`, `MissionTimeline`, `QueueList`, `UnitCard`, `BuildingCard`, `ResearchTreeNode`, `MapTile`, `SectorDetails`, `IntelReport`, `BattleReplay`, `MarketOrder`, `AllianceMember`, `ChatChannel`, `NotificationCenter`, `ConfirmDialog`, `ErrorPanel`, `AdminAuditRow`.

Jede Komponente braucht Loading/Empty/Error/Disabled/Success, Keyboard-Focus, Tooltip-Alternativen, DE/EN/VI/ES/TR und visuelle Regressionsscreenshot-Tests. Kontrast und Textgröße werden getestet, Icons zusätzlich mit Labels.

## 4. Typografie und Performance
- Zugelassene Open-Source-Schrift mit Lizenznotice oder System-Font-Stack, keine proprietären Fontdateien ins Nutzerpaket kopieren.
- PNG/WebP/AVIF responsive Größen, SVG für Symbole, verlustarme komprimierte Tiles, Sprite-Atlanten nur wenn eigener Assetnachweis.
- Keine komplett gerenderte 64×64-Karte für jedes Polling; Tiles/Viewport cachen. Reduced-motion-Option, keine blinken­den Zwangsanimationen.

## 5. QA / Recht
- `assets/MANIFEST.json`: `id,file,creator,license,source,created_at,reviewed,usage` für jedes Asset.
- Ein asset darf erst produktiv eingebunden werden, wenn Ursprung/Berechtigung klar und es auf Desktop/Mobile lesbar ist.
- Kein temporäres fremdes Grafikmaterial in Release-Bundles einschließen. Eigene Platzhalter nur als deutlich markierte **Asset-Arbeit**, nicht als spielmechanisch Fake-Funktion.
