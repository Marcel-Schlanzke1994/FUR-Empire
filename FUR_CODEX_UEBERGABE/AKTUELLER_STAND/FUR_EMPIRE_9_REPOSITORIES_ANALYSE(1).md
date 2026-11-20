# Quellenprüfung: neun Browser-Strategie-Repositories

Prüfdatum: **05.11.2026**. Die Dateibäume wurden vollständig auf der angegebenen Default-Branch erfasst, README-, Manifest- und Lizenzdateien untersucht und zentrale ausgewählte Engine-, Controller-, Datenbank- und Testdateien gelesen. **Dies ist keine Aussage, dass jede Quellcodezeile aller neun Repositories manuell geprüft oder jedes Projekt installiert und dynamisch getestet wurde.**

## 1. Reproduzierbare Versionsstände

| Repository | HEAD-Commit (Prüfung) | Code-Dateien/Assets insgesamt (Git-Blobs) | Status | deklarierte Lizenz |
|---|---|---:|---|---|
| [ioying/devana](https://github.com/ioying/devana) | `4e64e5a72c5ed00e94e1464992808d9e75f9cef1` | 241 | letzter Push 2014 | benutzerdefinierte permissive Bedingungen in `docs/license.txt` |
| [laserswald/Tribal-Wars-Open-Source](https://github.com/laserswald/Tribal-Wars-Open-Source) | `2bd72a062ea1ffa235e50e7d723f37df5b5c6eee` | 1.275 | archiviert | kein Root-LICENSE, CC BY-NC-ND 3.0 im PHP-Header |
| [ugml/php-client](https://github.com/ugml/php-client) | `acb7ae51c04cbebdd65d321633f4f71c910e4ba1` | 371 | letzter Push 2018 | AGPL-3.0 |
| [lanedirt/OGameX](https://github.com/lanedirt/OGameX) | `f61cbede42fe4a91cd7d25f8bac963f2804f3af5` | 3.075 | aktiv 2026 | MIT für den veröffentlichten Code, Artwork separat |
| [XGProyect/XGProyect](https://github.com/XGProyect/XGProyect) | `b3971d873f7512c62b4c981f285deb4d109349f4` | 1.282 | aktiv 2026 | GPL-3.0-only laut Composer |
| [XGProyect/XG-Proyect-v3.x.x](https://github.com/XGProyect/XG-Proyect-v3.x.x) | `612fe05945417552d2eee750761ff8c0ade454f5` | 2.865 | archiviert | GPL-3.0-only laut Composer |
| [XGProyect/XG-Proyect-v3.x.x-Languages](https://github.com/XGProyect/XG-Proyect-v3.x.x-Languages) | `945d1ec6ef2523327ea15208a080e6f5e90b1e53` | 268 | archiviert | GPL-3.0 |
| [XGProyect/legacy-versions](https://github.com/XGProyect/legacy-versions) | `44cb0f0b2ba7de13d9ec670b31931c8842b431db` | 42 | archiviert | kein übergreifendes Lizenzmanifest |
| [XGProyect/XG-Proyect-v2.10.x](https://github.com/XGProyect/XG-Proyect-v2.10.x) | `e9a088a36cb135ab2986c47aaad877838e7f2fdc` | 6.695 | archiviert | Root-`LICENSE.md` leer; Rechte unklar |

**Gesamtsumme:** 16.114 Git-Blobs. Nicht gleichbedeutend mit 16.114 unterschiedlichen Programmodulen: viele Dateien sind Bilder, Sprachdateien, Kopien historischer Versionen und Archive.

## 2. Einzelbewertungen mit überprüften Dateien

### Devana — Originalspielmechanik / Welt als Pixelraster
- Codebasis: PHP/MySQL, 52 PHP-Dateien, ein SQL-Schema, 241 Blobs. Die README weist ausdrücklich darauf hin, dass dieses GitHub-Repository kein offizielles Devana-Git ist.
- [Installationsanleitung](https://github.com/ioying/devana/blob/master/docs/readMe.txt): Ein Bild `grid.png` erzeugt mit Farben Wasser- und Landsektoren.
- [SQL-Schema](https://github.com/ioying/devana/blob/master/src/install/devana.sql): 25 `CREATE TABLE`-Definitionen; unter anderem `grid`, `nodes`, `modules`, `research`, `combat`, `trade`, `train`, `alliances`, `wars`, `messages` und `users`.
- [Spielregeln](https://github.com/ioying/devana/blob/master/src/core/game.php): Fraktionen, sechs Ressourcen, Kosten-/Geschwindigkeitsfaktoren, Forschung, Bau- und Produktionsdaten.
- [Kernlogik](https://github.com/ioying/devana/blob/master/src/core/core.php): Sitzungs-/Spielobjekte, `node::checkResources`, `checkResearch`, `checkBuild`, `checkTrain`, `checkCombat`, `doCombat` und Allianzoperationen.
- **Risiko:** Monolithische, veraltete PHP-Implementierung; im Kern ist z.B. SHA-1 für Passwortoperationen erkennbar; SQL wird teils per Verkettung aufgebaut. Nicht unbesehen übernehmen.
- **FUR:** Anleihen bei Land-/Wasser-Karten, Fraktionen, Siedlungs-/Außenpostensystem, frei konfigurierbarer Ressourcen- und Fortschrittsstruktur. Neuentwicklung mit Tests und Transaktionen.
- **Lizenz:** [docs/license.txt](https://github.com/ioying/devana/blob/master/docs/license.txt) erlaubt Nutzung/Änderung auch kommerziell unter Anforderungen zu Herkunft, Kennzeichnung von Änderungen und Erhalt des Lizenzhinweises. Konkrete Drittassets dennoch separat prüfen.

### Tribal-Wars-Open-Source — vorrangig Designarchiv
- Von 1.275 Blobs liegen 1.123 unter `graphic/`; 141 Dateien sind gebündelte Twig-Bibliothek. Kein relevantes vollständiges Backend.
- [index.php](https://github.com/laserswald/Tribal-Wars-Open-Source/blob/master/index.php) rendert eine Startseite; Registrierung und Authentifizierung fehlen trotz UI-Verweisen auf `register.php` und `index.php?action=login`.
- [merged/game.js](https://github.com/laserswald/Tribal-Wars-Open-Source/blob/master/merged/game.js) enthält alte jQuery-Funktionen, AJAX, Dialoge und UI-Helfer, aber keinen funktionierenden Spielscheduler.
- [global.php](https://github.com/laserswald/Tribal-Wars-Open-Source/blob/master/global.php) enthält den expliziten Hinweis auf CC BY-NC-ND 3.0. Kein `LICENSE`-Dokument im Root.
- **FUR:** Nur als historische Orientierung für die Informationsarchitektur (Karte, Einheitenübersicht, Berichte), keine Code-/Assetübernahme ohne separate Berechtigung.

### Ugamela / ugml/php-client — klare Schichtung, aber Alpha
- PHP 7.1/MariaDB-Ära; README warnt ausdrücklich vor Produktiveinsatz und nennt nicht implementierte Features.
- [Projektbeschreibung](https://github.com/ugml/php-client/blob/master/README.md) beschreibt getrennte `core/classes`, `controllers`, `models`, `views`, `templates`, `language`, `skins`.
- [Fleet-Model](https://github.com/ugml/php-client/blob/master/core/models/fleet.php) verwendet vorbereitete SQL-Anweisungen und enthält Versand-/Missionsoperationen.
- [Building-Model](https://github.com/ugml/php-client/blob/master/core/models/building.php) umfasst Gebäudevoraussetzungen und Buildqueue-Berechnungen.
- [SQL-Testschema](https://github.com/ugml/php-client/blob/master/tests/database.sql) enthält Planeten, Forschung, Flotten, Flüge und FK-Beziehungen.
- **Risiko:** Alpha, unvollständige Spielfunktionen, historische Abhängigkeiten.
- **FUR:** Serviceschnittstellen, getrennte UI/Controller/Domain-Ebenen, Datenmodell und Tests als Orientierung.
- **Lizenz:** [AGPLv3](https://github.com/ugml/php-client/blob/master/LICENSE). Bei Verwendung von AGPL-Code in einem veränderten netzwerkbasierten Werk entstehen besondere Pflichten zur Quellcodebereitstellung an die Benutzer. Deshalb im anfänglichen eigenständigen FUR-Kern nicht kopieren.

### OGameX — stärkste moderne Quellarchitektur
- 3.075 Blobs, davon ca. 300 in `app`, 128 in `tests`, 104 in `database`; Docker/CI, Laravel, Rust-Option.
- [README](https://github.com/lanedirt/OGameX/blob/main/README.md): Planeten, Gebäude, Forschung, Schiffe, Verteidigung, Highscores, Mondfunktionen, Expeditionen, Allianzen, Flottenmissionen.
- [composer.json](https://github.com/lanedirt/OGameX/blob/main/composer.json): PHP `^8.5`, Laravel `^13.0`, Fortify, Reverb, Spatie Permissions, Pest/PHPUnit/Larastan.
- [AttackMission.php](https://github.com/lanedirt/OGameX/blob/main/app/GameMissions/AttackMission.php): Validierung von Missionen, Ankunft, Kampfanwendung, Beute, Berichtserzeugung und Rückweg.
- [PhpBattleEngine.php](https://github.com/lanedirt/OGameX/blob/main/app/GameMissions/BattleEngine/PhpBattleEngine.php): rundenbasierter Kampf mit Einheitenzuständen; Rust-Alternative separat.
- [TestRaceConditionFleetDispatch.php](https://github.com/lanedirt/OGameX/blob/main/app/Console/Commands/Test/TestRaceConditionFleetDispatch.php): konkrete Race-Condition-Prüfung für parallele Flottenversendung.
- **FUR:** Domänenmodule, Missionslebenszyklus, Ereignisverarbeitung, Queue-Design, Sicherheits-/Parallelitätstests und Admin-Ebenen als primäre Architekturvorlagen.
- **Lizenz:** [MIT](https://github.com/lanedirt/OGameX/blob/main/LICENSE); Copyright-/Lizenzhinweise sind bei tatsächlicher Übernahme zu bewahren. **Die README weist ausdrücklich darauf hin, dass Artwork und Frontend-Rechte bei den ursprünglichen Rechteinhabern liegen.** Damit ist kein pauschales Wiederverwendungsrecht für die Spielbilder/Layouts belegt.

### XG Proyect 4 — Konfiguration, GameObjects, Administration
- Laravel 12, PHP `^8.2`, GPL-3.0-only; enthält neue `app`-Module und einen `legacy`-Bereich (hybride Migration).
- [GameObjectRegistry.php](https://github.com/XGProyect/XGProyect/blob/master/app/Core/GameObjects/GameObjectRegistry.php): Registrierung von Gebäuden, Forschung, Schiffen, Verteidigung, Offizieren; gruppierbare Objekttypen.
- [ProductionFormula.php](https://github.com/XGProyect/XGProyect/blob/master/app/Core/GameObjects/ProductionFormula.php): konfigurierbare Produktionsformeln.
- [routes/web.php](https://github.com/XGProyect/XGProyect/blob/master/routes/web.php): umfangreiche Administrationsrouten (Spieler, Sperren, Allianzen, Backups, Nachrichten, Forschung etc.).
- [README](https://github.com/XGProyect/XGProyect/blob/master/README.md): Laravel-Sail/DB-Installation.
- **FUR:** versioniertes Objektregister, Datenregelwerk, Admin-RBAC, Serverkonfiguration und Migration historischer Modelle.
- **Lizenz:** GPL-3.0-only laut [Composer](https://github.com/XGProyect/XGProyect/blob/master/composer.json); keine unbedachte Vermischung mit einem proprietären Produkt.

### XG Proyect 3 — historische modulare Vollimplementierung
- 2.865 Blobs; PHP 7.4+, älteres eigenständiges Core-/Entity-System, archiviert.
- [README](https://github.com/XGProyect/XG-Proyect-v3.x.x/blob/master/README.md) empfiehlt ausdrücklich XG Proyect 4 für Neuinstallationen.
- Codepfade: `app/Core/Entity/{PlanetEntity,FleetEntity,AllianceEntity,...}.php` sowie `app/Http/Controllers/Game/{Fleet1Controller,Fleet2Controller,Fleet3Controller,GalaxyController,...}.php`.
- **FUR:** Analyse klassischer Spielabläufe, Allianz- und Flotten-UX, Vergleich mit Version 4, keine Basis für moderne Dependency- oder Security-Entscheidungen.
- **Lizenz:** GPL-3.0-only laut [Composer](https://github.com/XGProyect/XG-Proyect-v3.x.x/blob/master/composer.json).

### XG Proyect 3 — Languages
- 268 Blobs, überwiegend PHP-Übersetzungsdateien in `english/`, `spanish/`, `turkish/`.
- Beispiel: `english/game/attack_lang.php`; Aufteilung nach Admin- und Spielbereichen.
- **FUR:** Strukturprinzip von sprach-/domänenspezifischen Übersetzungskatalogen. Eigene Texte und separate JSON-Übersetzungen statt Übernahme der GPL-Dateien.
- **Lizenz:** [GPL-3.0](https://github.com/XGProyect/XG-Proyect-v3.x.x-Languages/blob/master/LICENSE.md).

### XG Legacy Versions — Zeitarchiv
- 42 Blobs; 33 `.zip`, acht `.rar`, ein README. Kein direktes, einzelnes installierbares Standardprojekt im Root.
- **FUR:** Versionsvergleich, historische Regressionsfälle, alte Mechaniken als Forschungsgegenstand. Archive wurden katalogisiert, nicht sämtlich entpackt und ausgeführt.
- **Lizenz:** Kein Root-Lizenzmanifest. Jede Archivversion vor direkter Wiederverwendung prüfen.

### XG Proyect 2.10 — mehrfach archivierte Legacy-Entwicklung
- 6.695 Blobs, mehrere Versionsstände `src/2.10.0` bis `src/2.10.9` und duplizierte HTML/PHP/Grafikressourcen.
- Beispielpfade: `src/2.10.9/upload/includes/battle_engine/core/Battle.php`, `includes/classes/class.FlyingFleetHandler.php`, `includes/functions/PlanetResourceUpdate.php`.
- **FUR:** Historische Kampf- und Ressourcenformeln zu Vergleichs-/Regressionstests und Designanalyse heranziehen, nicht direkt transplantieren.
- **Lizenz:** leere Root-Datei `LICENSE.md`, GitHub-Metadaten `NOASSERTION`; Nutzungsrechte am Code nicht bestätigt.

## 3. Lizenzstrategie

1. FUR-Engine in erster Stufe original implementieren; Konzepte als Referenz, **nicht** wörtlich Quellcode übertragen.
2. Originalgrafiken und eigenes UI verwenden; keine OGame-/Tribal-Wars-Screenshots/Spielbilder als Produktassets verwenden.
3. Bei späterem MIT-Codeimport aus OGameX Dateiherkunft, Commit, SPDX-Hinweise, Lizenztext und Änderungen dokumentieren; gegebenenfalls bestehende Rechte dritter Parteien gesondert klären.
4. GPL-3.0-only und AGPL-3.0 nicht in einen als geschlossen vorgesehenen Engine-Kern kopieren. Wenn Open-Source-Lizenzierung geplant ist, Lizenzkombination und Veröffentlichungs-/Netzwerkpflichten bewusst prüfen.
5. Devana-Code nur nach konkreter Dateiprüfung und unter Einhaltung von Attribution/Änderungskennzeichnung erwägen; die ausdrücklichen Lizenzbedingungen nicht aus GitHub-`license=null` ableiten.
6. Bei unklaren Quellen (XG Legacy, v2, Tribal-Assets) Nutzung erst nach schriftlicher Freigabe oder belastbarer Rechteklärung.

Diese Hinweise sind technische Lizenzrisiko-Einschätzungen und ersetzen keine anwaltliche Prüfung.

## 4. Nutzungs-Matrix (jede Quelle liefert einen Beitrag)

| FUR-Subsystem | Primäre Referenz | Ergänzend | Umsetzung in v0.1 |
|---|---|---|---|
| Weltkarte, Territorien | Devana | Tribal (Layoutanalyse) | Einfache Rasterwelt, neue Grafik |
| Ressourcenproduktion | Devana, XG4 | Ugamela | Integergenaue Zeitproduktion |
| Bau-/Ausbildungsqueues | OGameX | Devana, Ugamela | persistente Events, je eine Queue |
| Forschung/Technologie | XG4 | XG3, Ugamela | zweistufiges Beispielregister |
| Missionen/Reisezeit | OGameX | XG2, XG3 | einfaches Raid-Event |
| Kampfberichte | OGameX | XG2, Devana | eigene Kampfregel und Reports |
| Spieler-/Allianzrollen | XG4 | XG3 | Rollen für v0.2 geplant |
| Übersetzungsstruktur | XG Languages | Ugamela | v0.2: neue Kataloge |
| Regression und historische Regeln | XG Legacy | XG2 | v0.2: Simulationsfixtures |
| Frontend-Informationsarchitektur | Tribal | OGameX | eigenständige UI |

## 5. Ergebnis

**Empfohlene Richtung:** FUR Empire als originelles, eigenes Spiel; OGameX und XG4 liefern starke moderne technische Vorbilder, Devana die stärkste Landspiel-Referenz. Die restlichen Quellen fungieren als Vergleich, Design- und Regressionstestsammlung. Ein direktes Verschmelzen aller Quellcodes ist technisch und lizenzrechtlich nicht sinnvoll.
