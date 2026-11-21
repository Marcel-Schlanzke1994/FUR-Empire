# Bericht zum Mehrsprachigkeitssystem

## Aktueller Stand

FUR Empire besitzt zentrale JSON-Sprachkataloge für Deutsch (`de`), Englisch (`en`), Spanisch
(`es`) und Französisch (`fr`). Alle vier Kataloge enthalten derzeit jeweils 292 Schlüssel. Ein
zusätzlicher Katalog für ältere Oberflächentexte enthält 804 identische Quellphrasen pro Sprache.
Diese Abdeckung ersetzt keine fachliche Prüfung der Übersetzungen und erfasst dynamisch
zusammengesetzte Texte nicht vollständig. Die
Sprachpräferenz wird serverseitig am Spielerprofil gespeichert und nach einem erneuten Login wieder
verwendet. Der Wechsel der Sprache beendet die Sitzung nicht.

Die neuen Bedienelemente des permanenten Chats sind in allen vier Katalogen vorhanden. Die
Fallback-Sprache ist Deutsch; unbekannte oder fehlende Schlüssel werden kontrolliert behandelt.

## Noch nicht abgenommen

Die verbindliche Vollübersetzung des gesamten Spiels ist noch nicht erreicht. Ein statischer Audit
der JavaScript-Oberfläche findet weiterhin zahlreiche deutsch fest eingebaute Texte, unter anderem
in älteren Spiel-, Community-, Moderations- und Verwaltungsabläufen. Gleiche Schlüsselzahlen allein
belegen daher keine vollständige Übersetzung.

Bis diese Texte in zentrale Schlüssel überführt, fachlich in alle vier Sprachen übersetzt und in den
jeweiligen Spielerabläufen geprüft sind, bleiben die folgenden Definition-of-Done-Punkte offen:

- vollständige Nutzbarkeit aller wichtigen Abläufe auf Englisch, Spanisch und Französisch;
- lokalisierte dynamische Spiel-, Fehler- und Erfolgsmeldungen;
- Prüfung langer Übersetzungen und sprachabhängiger Pluralformen;
- vollständige visuelle Prüfung jeder Sprache auf Desktop und Mobilgeräten.

## Prüfverfahren

Die Kataloge werden als JSON eingelesen und auf gleiche Schlüsselmengen geprüft. Zusätzlich muss
der Frontend-Quelltext auf sichtbare Literale untersucht werden. Die abschließende Abnahme erfordert
automatisierte Ablaufprüfungen und eine manuelle Prüfung der vier Sprachen; technische
Übersetzungsschlüssel dürfen dabei nie sichtbar sein.
