# Neutrale Warenbörse — FUR-NEUTRAL-MARKET-1

Implementiert, ungetestet. Phase A; keine Aussage zur abgenommenen Balance.

Im Bereich **Handel** stehen Holz, Stein, Erz, Verbundlegierung, Schaltmodule,
Fasergewebe, Feldrationen, Medizinsätze, Schmiermittel und Schutzkeramik zur Wahl.
Die ersten drei Güter verwenden die bisherigen Rohstoffkonten. Die sieben
Materialwaren liegen in `goods_inventory` der aktiven Kolonie. Sie bleiben dort
bei Welt-/Koloniewechsel und Neustart erhalten; es gibt keinen freien Transfer
zwischen Kolonien oder Ebenen. Energie bleibt ein künftiger Leistungswert.

Der Austausch verwendet ganzzahlige Warenwerte aus
`fur_empire/rules/neutral-market-1.json`:

`Zielmenge = floor(Quellmenge × Quellwert × Auszahlung / (100 × Zielwert))`.

Standardauszahlung 50 %, nach verbindlicher Syndikatwahl 60 %. Holz, Stein und
Erz haben jeweils Wert 1; damit bleibt ihr bisheriger Wechselkurs erhalten.
Beispiel: 100 Holz ergeben 4 Verbundlegierungen (Wert 12). Zehn
Verbundlegierungen ergeben beim Standardkurs 60 Holz. Rundung und Abschlag
verhindern einen positiven Hin-/Rücktauschkreislauf. Mindestmenge 10,
Höchstmenge 100.000; Quellvorrat, mindestens eine Zieleinheit und Depotplatz
werden vor jeder Änderung serverseitig geprüft. Je Gut gilt dieselbe
Einheitenkapazität `2000 + 2000 × Depotstufe`. Die bestehenden Rohstoffreserven
bleiben separat; ein Tausch darf das Zieldepot nicht überfüllen.

Die Vorschau im Browser ist unverbindlich. Der Server prüft Preis, Fraktion,
Menge und Vorräte erneut. Ein authentifizierter, CSRF-geschützter Befehl läuft
mit bestehender Idempotenz in derselben Transaktion wie Kolonie, Rohstoffledger,
Audit und unveränderlicher Warenbeleg. Jeder Beleg speichert Welt, Kolonie,
Version, Regelhash sowie alle zehn Vorher-/Nachherbestände. Materialwaren geben
in dieser Regelversion keine Produktions-/Kampfboni; ihre weitere Verwendung
in Rezepten und Logistik ist noch nicht implementiert.

Ein Abbruch existiert beim sofortigen Tausch nicht. Derselbe Befehlsschlüssel
wirkt einmal; anderer Inhalt unter demselben Schlüssel wird abgelehnt.
Kolonieaufgabe ist bei verbliebenen Materialwaren gesperrt: vorher zurücktauschen.
Der eigene Datenexport enthält das lokale Wareninventar. SVG-Ausfall verhindert
weder Lesen der Mengen noch Tausch, da alle Informationen als Text vorliegen.

Offen: Phase-B-Abnahme auf SQLite/PostgreSQL, Mobile/Tastatur/Screenreader,
vollständige fünfsprachige Texte, Preisbalance und spätere Materiallogistik.
