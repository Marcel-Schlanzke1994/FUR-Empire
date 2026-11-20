# FUR EMPIRE — NEUN REFERENZQUELLEN, CODEPROVENIENZ UND LIZENZGRENZEN

**Stand:** 06.11.2026. GitHub-Repositories im vorigen Architektur-Review anhand von API-Metadaten, Dateibäumen und repräsentativen zentralen Dateien ausgewertet. Nicht jede fremde Zeile und jedes einzelne Asset wurde juristisch auditiert. Das Quellenverzeichnis ist **Design-Recherche**, keine pauschale Codefreigabe.

| Kürzel | Repo / geprüfter Hauptstand | Lizenz laut Repository bzw. Dateien | Verwendbarer Erkenntnisbereich | Direkter Copy-Paste-Status |
|---|---|---|---|---|
| D | [ioying/devana](https://github.com/ioying/devana) · `4e64e5a72c5ed00e94e1464992808d9e75f9cef1` | `docs/license.txt`: eigener permissiver Lizenztext, inklusive Attribution, Markierung von Änderungen und Copyright-Hinweis | 2D-Raster, Fraktionen, modularer Basenausbau, Krieg/Frieden, Ressourcen, Kampfsimulator | Nur nach Einzeldatei-/Provenienzprüfung und Einhaltung der Lizenzauflagen |
| TW | [laserswald/Tribal-Wars-Open-Source](https://github.com/laserswald/Tribal-Wars-Open-Source) · `2bd72a062ea1ffa235e50e7d723f37df5b5c6eee` | Kein Repo-Lizenzfeld; eigene PHP-Header nennen CC BY-NC-ND 3.0; Assets zudem unklar | Historische UI-Referenz, Karten-/Allianzbildschirm als Analyseobjekt | **Nicht kopieren** |
| U | [ugml/php-client](https://github.com/ugml/php-client) · `acb7ae51c04cbebdd65d321633f4f71c910e4ba1` | AGPL-3.0 | MVC-Struktur, Datenobjekte, Fleet/Building/Research, Tests | Nicht in proprietären/anders lizenzierten Kern übernehmen; Anforderungen der AGPL gesondert prüfen |
| OGX | [lanedirt/OGameX](https://github.com/lanedirt/OGameX) · `f61cbede42fe4a91cd7d25f8bac963f2804f3af5` | MIT für eigenes Backend; README erklärt Gameforge-Rechte an Artwork und Frontend | Missionsklassen, Eventserver, PHP/Rust-Kampf, Race-Tests, Planet/Forschung/Flotte | MIT-Code ggf. mit Notices; **Artwork und Drittinhalte nicht kopieren** |
| X4 | [XGProyect/XGProyect](https://github.com/XGProyect/XGProyect) · `b3971d873f7512c62b4c981f285deb4d109349f4` | GPL-3.0 | GameObjectRegistry, Entwicklung, Shop/Administration, Backup, Settings | Kein Import ohne explizite GPL-Veröffentlichungsstrategie |
| X3 | [XGProyect/XG-Proyect-v3.x.x](https://github.com/XGProyect/XG-Proyect-v3.x.x) · `612fe05945417552d2eee750761ff8c0ade454f5` | GPL-3.0, archiviert | Missionen, Forum, Diplomatie, Flotten/Allianzen | Kein Import ohne GPL-Plan |
| X3L | [XGProyect/XG-Proyect-v3.x.x-Languages](https://github.com/XGProyect/XG-Proyect-v3.x.x-Languages) · `945d1ec6ef2523327ea15208a080e6f5e90b1e53` | GPL-3.0 | Übersetzungsstruktur, Locale-Trennung | Texte selbst neu schreiben/übersetzen |
| XL | [XGProyect/legacy-versions](https://github.com/XGProyect/legacy-versions) · `44cb0f0b2ba7de13d9ec670b31931c8842b431db` | Kein konsistentes Repository-Lizenzfeld; enthält historische Archive | historische Architekturvergleiche, keine moderne Laufzeitbasis | Einzelarchiv nicht ohne Prüfung nutzen |
| X2 | [XGProyect/XG-Proyect-v2.10.x](https://github.com/XGProyect/XG-Proyect-v2.10.x) · `e9a088a36cb135ab2986c47aaad877838e7f2fdc` | GitHub 'Other'; `LICENSE.md` im geprüften Checkout leer | historische Kampf- und Flottenrechenmodelle | **Nicht kopieren**, Rechte unklar |

## Grundlegende Lizenzentscheidung

**FUR-Grundcode = eigenständige Implementierung.** Mechanikgattungen (Bauwarteschlange, Fleet-Mission, Forschung, strategische Karte) können konzeptionell untersucht werden; Quelltext, spezifische Assets, Logos, originalsprachliche Texte und rechtlich geschützte Eigenheiten dürfen nicht gedankenlos kopiert werden. MIT-Code kann im Einzelfall übernommen werden, wenn alle Urheber-/Lizenzhinweise und Dritt-Abhängigkeiten erhalten bleiben. GPL/AGPL-Lizenzen können Copyleft- bzw. Quellcodebereitstellungspflichten auslösen; das ist vor einer echten Übernahme mit einer geeigneten Rechts- und Projektstrategie zu entscheiden. CC BY-NC-ND und fremde geschützte Grafiken werden nicht verwendet.

## Agentenpflichten bei jedem importierten Fremdasset/-paket

1. Erzeuge/aktualisiere `third_party/PROVENANCE.json` mit `repo`, `commit`, `file`, `author`, `license`, `modifications`, `notice_required`, `copyright_claims`, `risk`, `reviewed_by`.
2. Automatischer License-/Dependency-Scanner; Notices in `THIRD_PARTY_NOTICES.md` und ggf. `/legal/licenses` verfügbar.
3. Fehlende Lizenzfreigabe → eigenständig implementieren oder eigenes Asset erzeugen; niemals fremde Bilder als vorläufige Produktionsplatzhalter einbauen.
4. Originelles FUR-Branding, neue Kommandanten-/Fraktions-/Planeten- und Schiffsbezeichnungen, eigener UI-Stil und eigene Lore.
5. Rechte auf User-FUR-Assets und mögliche Community-Beiträge vor der Veröffentlichung prüfen; Upload-Lizenzen und Entfernen-/Report-Prozess dokumentieren.

**Hinweis:** Dies ist eine technische Lizenzinventarisierung und keine anwaltliche Entscheidung darüber, welche konkrete Mischung rechtlich zulässig wäre.
