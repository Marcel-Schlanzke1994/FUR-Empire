# FUR EMPIRE — EIGENTÜMERÜBERGABE UND ABNAHME NACH DER IMPLEMENTIERUNG

## Was als vollständig lokal fertig gilt
- Jede Feature-ID aus `spec/FEATURES.json`: fachliche Umsetzung, UI, Datenhaltung, Sicherheitsprüfung, übersetzte Texte/Hilfe, automatisierter Test, Ergebnisbeleg und `verified`.
- Frischer Checkout startet ohne manuelle Programmierung via dokumentierten Compose-/CLI-Befehlen; ohne Live-SMTP laufen Test-Mails sicher in einem Mailcatcher.
- Testdaten/QA-Accounts können isoliert gelöscht werden, ohne eine echte Nutzerwelt zu gefährden. Kein Fake-Gameplay.
- Zwei Spieler und zwei Welten lassen sich live gegeneinander testen; sämtliche Wirtschaftsketten, Events, War/Alliance, Terra/Orbit, Saisons und Admin-Prozesse funktionieren unter wiederholter Last.
- Release umfasst dokumentierten Restore-Test, Sicherheitsreport, Lasttest, Lizenz-/Assetregister und einen neuen Release-Tag.

## Was erst nach deiner Rückkehr benötigt wird
| Externe Aktion | Agent kann vorher erledigen | Betreiber macht später |
|---|---|---|
| Domain | DNS-Vorlage, Reverse-Proxy, TLS-ACME-Config und Test-Domain-Konfig | Domain kaufen, Registrar/DNS-Zugang bereitstellen |
| VPS/Root | Serveranforderungen aus gemessenem Lastprofil, Compose-/IaC-Deploy, Hardening-Runbook | Host auswählen, Vertrag/Server bestellen, SSH-Zugang sicher einrichten |
| HTTPS | TLS-Config und interne Stagingtests | DNS auf Host zeigen lassen und Live-Zertifikat prüfen |
| SMTP | Mailcatcher, E-Mail-Templates, SMTP-Adapter | Provider, Domain-Sender, SPF/DKIM/DMARC konfigurieren |
| Rechtliches | Mustervorlagen/Platzhalter und Datenfluss-Dokumentation | Rechtskonforme Impressum/Datenschutz/AGB/Jugendschutz prüfen/freigeben |
| Secrets | Variablenschema, Generierungsskripte, `.env.example` | Produktive Secrets generieren, sicher einspielen und alte veröffentlichte Tokens rotieren |
| Admin-Freigabe | Rollen/TOTP/Account-Onboarding testen | Eigene Adminidentität final bestätigen, TOTP einrichten |
| Live-Freigabe | Gates, Restore-, Performance-, Security-Reports | Belastbaren Go-Live-Beschluss treffen und Deployment genehmigen |

## Eigentümer-Abnahmetest (real, nicht nur Screenshots)
1. Neue Welt erstellen, Account A/B registrieren, Regeln-/Beginnerschutz-/Fraktionen prüfen.
2. Wirtschafts- und Bauaktionen ausführen, schließen/neu öffnen, Serverworker stellt Queues fertig.
3. Karte mit NPC-PvE, Spionage, Allianz-PvP und Gemeinsamem Angriff testen, echte Logs und Verluste nachvollziehen.
4. Mehrkolonien und Transport einschließlich vollen Depots/Ressourcenreserve testen.
5. Orbit freischalten, Flotte senden, Mond/Station/Bergung/Expedition gegen echte DB-Events prüfen.
6. Saison-Event/Weltboss starten, Saisonabschluss, Dauerwelt bleibt intakt.
7. Security: falscher Nutzer kann keine fremde Kolonie lesen/manipulieren, doppelte Marktannahme erfolgt nur einmal, TOTP kann nicht repliziert werden.
8. Backup in separater Testinstallation wiederherstellen und Ergebnisse vergleichen.
9. Erst nach allen Schritten öffentliche Domain und Echtgeld-/Live-Integrationen gesondert freigeben.

**Wichtig:** Auch wenn der Agent alles implementiert, ist ein öffentlicher Start nie nur ein Domainkauf. Host-Sicherheit, Supportkapazität, Moderation, Lastprofil, Betreiberpflichten und laufende Updates bleiben dauerhafte Aufgaben.
