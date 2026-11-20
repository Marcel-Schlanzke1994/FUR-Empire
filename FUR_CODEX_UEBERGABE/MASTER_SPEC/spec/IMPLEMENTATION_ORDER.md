# FUR EMPIRE — AGENT BUILD ORDER

Epics werden nach Abhängigkeit abgearbeitet; alle Feature-IDs sind verpflichtend, auch P2.

## E00 — Audit & Lizenz

Abhängigkeiten: keine; 0 primär zugeordnete Feature-IDs.



## E01 — Infrastruktur / CI

Abhängigkeiten: E00; 6 primär zugeordnete Feature-IDs.

OPS-001, OPS-002, OPS-003, OPS-005, OPS-006, OPS-007

## E02 — Identität / Welten / Datenschutz

Abhängigkeiten: E01; 20 primär zugeordnete Feature-IDs.

F2-001, F2-002, F2-003, F2-004, F2-005, F2-006, F2-007, ACC-001, ACC-002, ACC-003, ACC-004, ACC-005, ACC-006, ACC-007, ACC-008, ACC-009, ACC-010, ENG-001, ENG-002, ENG-003

## E03 — FUR-2-Migration / Ledger

Abhängigkeiten: E02; 53 primär zugeordnete Feature-IDs.

F2-008, F2-009, F2-010, F2-011, F2-012, F2-013, F2-014, F2-015, F2-016, F2-017, F2-018, F2-019, F2-020, F2-021, F2-022, F2-023, F2-024, F2-025, F2-026, F2-027, F2-028, F2-029, F2-030, F2-031, F2-032, F2-033, F2-034, F2-035, F2-036, F2-037, F2-038, F2-039, F2-040, F2-041, F2-042, F2-043, F2-044, F2-045, F2-046, F2-047, F2-048, F2-049, F2-050, F2-051, F2-052, F2-053, F2-054, F2-055, F2-056, F2-057, F2-058, F2-059, F2-060

## E04 — Zeit-Engine / Queues

Abhängigkeiten: E03; 14 primär zugeordnete Feature-IDs.

ENG-004, ENG-005, ENG-006, ENG-007, ENG-008, ENG-009, ENG-010, ENG-011, ENG-012, ENG-013, ENG-014, ENG-015, ENG-016, ENG-017

## E05 — Terra-Karte / Mehrkolonien

Abhängigkeiten: E04; 25 primär zugeordnete Feature-IDs.

W01, W02, W03, W04, W05, W06, W07, W08, W09, W10, TERRA-001, TERRA-002, TERRA-003, TERRA-004, TERRA-005, TERRA-006, TERRA-007, TERRA-008, TERRA-009, TERRA-010, TERRA-011, TERRA-012, TERRA-013, TERRA-014, TERRA-015

## E06 — Wirtschaft / Gebäude / Forschung

Abhängigkeiten: E05; 24 primär zugeordnete Feature-IDs.

E01, E02, E03, E04, E05, E06, E07, E08, ECO-001, ECO-002, ECO-003, ECO-004, ECO-005, ECO-006, ECO-007, ECO-008, ECO-009, ECO-010, ECO-011, ECO-012, ECO-013, ECO-014, ECO-015, ECO-016

## E07 — Kampf-Engine / Units

Abhängigkeiten: E06; 25 primär zugeordnete Feature-IDs.

K01, K02, K04, K12, K14, WAR-001, WAR-002, WAR-003, WAR-004, WAR-005, WAR-006, WAR-007, WAR-008, WAR-009, WAR-010, WAR-011, WAR-012, WAR-013, WAR-014, WAR-015, WAR-016, WAR-017, WAR-018, WAR-019, WAR-020

## E08 — Missionen / Spionage / Fernkampf

Abhängigkeiten: E07; 9 primär zugeordnete Feature-IDs.

K03, K05, K06, K07, K08, K09, K10, K11, K13

## E09 — Allianz / Diplomatie

Abhängigkeiten: E08; 20 primär zugeordnete Feature-IDs.

A01, A02, A03, A04, SOC-001, SOC-002, SOC-003, SOC-004, SOC-005, SOC-006, SOC-007, SOC-008, SOC-009, SOC-010, SOC-011, SOC-012, SOC-013, SOC-014, SOC-015, SOC-016

## E10 — Sozial / Berichte / Moderation

Abhängigkeiten: E09; 4 primär zugeordnete Feature-IDs.

A05, A06, A07, A08

## E11 — NPC / Quests / Endgame

Abhängigkeiten: E08; 20 primär zugeordnete Feature-IDs.

P01, P02, P04, PVE-001, PVE-002, PVE-003, PVE-004, PVE-005, PVE-006, PVE-007, PVE-008, PVE-009, PVE-010, PVE-011, PVE-012, PVE-013, PVE-014, PVE-015, PVE-016, PVE-017

## E12 — Orbit Welten / Kolonien

Abhängigkeiten: E11; 10 primär zugeordnete Feature-IDs.

ORB-001, ORB-002, ORB-003, ORB-004, ORB-005, ORB-006, ORB-007, ORB-008, ORB-009, ORB-010

## E13 — Orbit Flotten / Kampf

Abhängigkeiten: E12; 22 primär zugeordnete Feature-IDs.

ORB-011, ORB-012, ORB-013, ORB-014, ORB-015, ORB-016, ORB-017, ORB-018, ORB-019, ORB-020, ORB-021, ORB-022, ORB-023, ORB-024, ORB-025, ORB-026, ORB-027, ORB-028, ORB-029, ORB-030, ORB-031, ORB-032

## E14 — Inventar / Handel / Helden

Abhängigkeiten: E13; 12 primär zugeordnete Feature-IDs.

P06, ITEM-001, ITEM-002, ITEM-003, ITEM-004, ITEM-005, ITEM-006, ITEM-007, ITEM-008, ITEM-009, ITEM-010, ITEM-011

## E15 — Saisons / LiveEvents / Ranking

Abhängigkeiten: E14; 16 primär zugeordnete Feature-IDs.

P03, P05, PVE-018, SEAS-001, SEAS-002, SEAS-003, SEAS-004, SEAS-005, SEAS-006, SEAS-007, SEAS-008, SEAS-009, SEAS-010, SEAS-011, SEAS-012, SEAS-013

## E16 — Administration / Anti-Abuse

Abhängigkeiten: E15; 21 primär zugeordnete Feature-IDs.

T04, T08, ADM-001, ADM-002, ADM-003, ADM-004, ADM-005, ADM-006, ADM-007, ADM-008, ADM-009, ADM-010, ADM-011, ADM-012, ADM-013, ADM-014, ADM-015, ADM-016, ADM-017, ADM-018, ADM-019

## E17 — Design / Mobile / i18n

Abhängigkeiten: E16; 12 primär zugeordnete Feature-IDs.

T05, T06, UX-001, UX-002, UX-003, UX-004, UX-005, UX-006, UX-007, UX-008, UX-009, UX-010

## E18 — Realtime / Integrationen

Abhängigkeiten: E17; 9 primär zugeordnete Feature-IDs.

T07, UX-011, UX-012, UX-013, UX-014, UX-015, UX-016, UX-017, UX-018

## E19 — Sicherheit / Datenschutz / Betrieb

Abhängigkeiten: E18; 13 primär zugeordnete Feature-IDs.

T01, T02, T03, OPS-004, OPS-008, OPS-009, OPS-014, OPS-015, OPS-016, OPS-017, OPS-018, OPS-023, OPS-024

## E20 — Vollständige QA & Performance

Abhängigkeiten: E19; 5 primär zugeordnete Feature-IDs.

OPS-010, OPS-011, OPS-012, OPS-013, OPS-022

## E21 — Betriebsbereites Handoff

Abhängigkeiten: E20; 4 primär zugeordnete Feature-IDs.

T09, OPS-019, OPS-020, OPS-021

