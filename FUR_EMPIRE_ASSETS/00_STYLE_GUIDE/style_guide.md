# FUR EMPIRE Grafikstandard

## Materialien und Licht

Die Palette in [palette.json](palette.json) gibt den Ton vor. Dunkles Navy und Anthrazit bilden die großen Flächen. Gebürstete Goldkanten markieren Übergänge, Wappen und die Hierarchie der Architektur. Cyan sitzt an Energiepfaden, Schilden und Sensoren. Terra verwendet zusätzlich Pflanzen-, Fels- und Himmelsfarben, Orbit sparsam planetare und kosmische Akzente.

Das Hauptlicht kommt von oben links. Kanten sind warm, Schatten kühl. Materialwechsel von Stahl zu Keramik, Glas, Textil oder Fell bleiben auch auf verkleinerten Motiven lesbar.

## Silhouette und Kamera

Terra-Gebäude und Außenposten haben eine leicht erhöhte Front-Rechts-Dreiviertelansicht. Eine integrierte Platte darf zur Konstruktion gehören. Infanterie zeigt Körper, Ohren und Ausrüstung vollständig. Maschinen bleiben als Maschinen erkennbar. Orbit-Schiffe zeigen den Bug links unten, den Treibsatz rechts oben und die Oberseite. Flache Schiffsjäger, breite Träger, modulare Frachter und große Kommandoschiffe verwenden unterschiedliche Grundformen.

Die drei Referenzen führen die Bildsprache. Das frontale symmetrische Markenwappen folgt der schriftlichen Vorgabe. Die Terrain-Projektion folgt dem quadratischen Terra-Raster. Die technischen Atlas-Kacheln und Masken nutzen eine senkrechte Kartenansicht.

## Anwendung

Rasterwerte und Dateipfade stehen im [Asset-Manifest](asset_manifest.json). Freisteller verwenden RGBA mit gerader Alpha-Transparenz. Transparente WebP-Exporte sowie Karten-, UI-Textur- und Effektdateien sind verlustfrei. Breite Titelbilder, Banner und Illustrationen verwenden lossy WebP und PNG.

Navigations- und Aktionsicons nutzen `currentColor` für die eingebettete 24er-SVG-Version. Kartenmarker haben getrennte Gruppen für Eigentümerfarbe, Symbol und Auswahlrahmen. Bei Inline-SVG lässt sich `--owner` für die Spielerfarbe und `--selected` für die Sichtbarkeit des Auswahlrahmens setzen. Die Allianzbauteile teilen die ViewBox 512 × 512 und werden übereinander positioniert. `--shield-fill`, `--shield-rim` und `--symbol-color` steuern die eingebetteten Farben. Die Ladeanzeige respektiert `prefers-reduced-motion`.

## Gelände und Effekte

Kantenmaske und Positionen stehen in [terrain_transitions.json](../01_TERRA/terrain/atlases/terrain_transitions.json). Die Bits N=1, E=2, S=4 und W=8 bezeichnen Nachbarn derselben Geländefamilie. Kanten mit nicht gesetztem Bit enden in Ebene, und vier Kacheln teilen das gleiche Eckprofil. Je Familie entspricht die Variante 15 dem zugehörigen Grundfeld. Die Nominalposition des Festungsfußes liegt bei (256, 444). Der beschädigte Zustand liegt über dem Festungssprite und der zerstörte Zustand ersetzt ihn am selben Anker.

Die Effektatlanten laufen zeilenweise von links oben. Der Anker liegt jeweils bei (128, 128) relativ zum Frame. Jede JSON-Datei enthält Dauer, Indizes und Rechtecke. Der letzte Frame ist leer und beendet die Einmalanimation.

## Quellen und Formate

Die Quellenzuordnung und Werkzeugangaben stehen im [Referenzindex](reference_index.md). Die artbezogenen Originale liegen unter `03_SOURCE_FILES`. Vektor-SVGs sind direkt editierbar. OpenRaster-Dateien stellen die wirklich vorhandenen Kompositionsebenen bereit. Bildgenerierte Master bleiben flache PNGs in ihrer ursprünglichen Auflösung.
