# Bericht zur Asset-Integration

## Umfang und Ergebnis

Die verbindlichen Quellpakete `FUR_EMPIRE_ASSETS/01_TERRA` und
`FUR_EMPIRE_ASSETS/02_ORBIT` wurden rekursiv geprüft, ohne Quelldateien zu verändern oder zu
löschen.

| Paket | Grafikdateien | Quellbytes | Identische Laufzeitkopien | Ungeklärt |
| --- | ---: | ---: | ---: | ---: |
| Terra | 280 | 34.917.309 | 280 | 0 |
| Orbit | 226 | 129.562.207 | 226 | 0 |
| **Gesamt** | **506** | **164.479.516** | **506** | **0** |

Alle PNG-, WebP- und SVG-Exporte besitzen byteidentische Laufzeitkopien unter
`static/assets/game/terra` beziehungsweise `static/assets/game/orbit`. Sämtliche Pfade des zentralen
Katalogs sind erreichbar. Er fasst die Exporte zu 302 Motiven zusammen (169 Terra, 133 Orbit) und
bietet 288 eindeutige Aliase. WebP wird für Rastergrafiken, SVG für skalierbare Symbole bevorzugt;
der Originalexport bleibt der letzte Fallback.

Der vollständige Einzeldateibericht liegt in [asset-inventory.json](asset-inventory.json). Jeder
Datensatz enthält Quellpfad, Laufzeitziel, Format, tatsächliche Abmessungen, Dateigröße, SHA-256,
Katalogschlüssel, vorgesehenen Spielbereich, Integrationsstatus und gegebenenfalls einen konkreten
Ablehnungsgrund. Der aktuelle Bestand enthält keine ungeklärte Grafik.

```powershell
.\.venv\Scripts\python.exe scripts\generate_asset_inventory.py
```

Der Generator benötigt nur die Standardbibliothek und verändert weder Sperrdateien noch Quellassets.

## Laufzeitintegration

- Öffentliche und angemeldete Oberfläche nutzen Wortmarke, Favicon und responsive Titelgrafiken.
- Terra-Navigation, Ressourcen, Gebäude, Forschung, Einheiten, Inventar, Leerzustände, Gelände,
  Sichtzustände, Außenposten, Kartenobjekte und Missionsmarker werden zentral aufgelöst.
- Orbit-Zugang, System- und Kolonieansichten verwenden Orbit-Titel, Planeten, Schiffe und
  Orbitalobjekte.
- Spielereingaben bilden niemals ungeprüfte Dateipfade.
- Dynamische Bilder verwenden Lazy Loading und asynchrone Dekodierung. CSS erhält Seitenverhältnisse
  und responsive Größen; bei Katalogfehlern bleibt ein Text-/Symbolfallback.
- Stabile `/static`-Pfade erlauben Browser- und Proxy-Caching ohne lokale Windows-Pfade.

Varianten wie Animationsblätter, kosmetische Embleme und alternative Effekte bleiben katalogisiert,
auch wenn ihr Spielzustand momentan nicht dargestellt wird. Normale Ansichten laden sie nicht.

## Nicht öffentliche Paketdateien

`01_TERRA/PACKAGE_MANIFEST.json`, `01_TERRA/damage_overlays/placement.json` und
`02_ORBIT/PACKAGE_MANIFEST.json` sind Produktionsmetadaten, keine Browsergrafiken. Sie bleiben
unverändert in den Quellordnern.

## Tatsächlich ausgeführte Prüfung

- Rekursives Format-, Größen- und Byteinventar
- SHA-256-Vergleich jeder Quellgrafik mit ihrer Laufzeitkopie
- Abmessungs- und Katalogabgleich für PNG, WebP und SVG
- Existenzprüfung jedes Katalogpfades
- Ruff und Black für den Inventargenerator
- Desktop- und mobile Headless-Chrome-Prüfung der Landingpage; die gefundene
  Überschriftenüberlappung wurde behoben

Eine manuelle Mehrgeräteabnahme sämtlicher 506 Varianten wird damit nicht behauptet.
