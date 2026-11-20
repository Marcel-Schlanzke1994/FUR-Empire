# Qualitätsprüfung

Geprüft am 18. November 2026. Das Asset-Manifest führt den Status und die Prüfschritte je Motiv.

| Prüfung | Ergebnis |
| --- | --- |
| Katalog | 302 Motive in Terra und Orbit |
| Freigegeben in der Produktionsprüfung | 302 |
| Formate, Abmessungen, SVG-Rendering und Alpha | 302 von 302 Motiven bestanden |
| Geländekacheln | 48 Varianten, 1632 pixelgenau passende Kantenpaare, PNG/WebP pixelgleich |
| Effekte | 5 Spritesheets mit je 16 einzigartigen Frames, JSON-Rechtecke und Anker geprüft |
| OpenRaster | 21 geprüfte Originaldateien |
| Browser | 152 Ressourcen je Lauf in Chrome dekodiert, Markerfarben und reduzierte Animation geprüft |

## Native Auflösungen und Bearbeitbarkeit

Jeder Export hat die im Manifest ausgewiesene Größe. Native PNG-Master halten die vom Generierungswerkzeug gelieferte Auflösung fest. Die Tabelle nennt Hochrechnungen aus Einzelmastern.

| Motiv | Nativer Master | Spielauflösung |
| --- | ---: | ---: |
| terra_title | 1672 × 941 | 2560 × 1440 |
| orbit_title | 1672 × 941 | 2560 × 1440 |
| space_stars | 1672 × 941 | 3840 × 2160 |
| space_nebula | 1672 × 941 | 3840 × 2160 |
| space_frontier | 1672 × 941 | 3840 × 2160 |

SVG-Dateien enthalten editierbare Pfade. Bei OpenRaster sind die tatsächlich erzeugten Bestandteile als Ebenen vorhanden. Die übrigen generativen PNG-Master sind flach.

Die Browserprobe lädt die Grafiken als eigenständige Ressourcen auf einer lokalen Testseite.

## Offene oder abgelehnte Motive

Keine offenen Katalogeinträge.
