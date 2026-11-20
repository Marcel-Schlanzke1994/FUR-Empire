# Performance report — bootstrap status

- Prior documented read-only smoke: 120 local HTTP GET requests with 12 concurrent clients, all successful (`docs/VERIFICATION.md`). This is not a public load or endurance test.
- Existing concurrency regression: 100 concurrent resource transfers are covered by the multiplayer suite; the isolated PostgreSQL suite passed in the E00 baseline.
- No new 30-minute load run, 2–10-account/two-world browser journey, or Orbit-scale capacity test was run for this start-prompt turn.
- No throughput, percentile latency, CPU, memory, or capacity claims are made for the 344-feature design.

**Status:** baseline evidence only; E20 performance gate remains open.


- The staging smoke performs health/readiness, login, state and one build command sequentially. It validates correctness only; latency, concurrency, throughput, resource utilization and endurance were not measured.


## E05 multi-colony runtime update (2026-11-06)

The full disposable PostgreSQL 18 integration suite passed 115 tests with one SQLite-only skip after migration 005. This is correctness evidence, not a throughput or endurance result. Colony simulation is now performed for each owned base; 30-minute load and multiworld performance gates remain open.


## E05 W07 worker scan note — 2026-11-06

Neutral stock refill stores a per-world check timestamp and scans a world no more than once per minute, rather than once per worker second. Correctness was tested on SQLite and disposable PostgreSQL 18. No throughput or endurance benchmark was run for this change; E20 performance gates remain open.


## E05 W08 region summary — 2026-11-06

The region summary is derived from existing world outposts and cached in the Game instance and validated against each current world ownership snapshot; no migration or persistent schema change was made. Focused SQLite correctness passed. No performance benchmark was run, so latency and load impact are unmeasured and E20 gates remain open.


## E05 regional cap correctness — 2026-11-06

The bonus cap is derived as 16 regions x 2 percentage points; no persistence or migration was added. Correctness tests pass. No benchmark was run; no performance claim is made.

## E05 TERRA-009 colony abandonment — 2026-11-06

Abandonment scans the source colony jobs, same-world colony jobs for inbound supply, and open escrow offers before transactional deletion. Focused correctness tests passed on SQLite and disposable PostgreSQL 18. No latency, concurrency-under-load, or throughput benchmark was run; E20 performance gates remain open.

## E05 TERRA-012 per-world bookmark cap — 2026-11-06

The quota count is scoped by the indexed `(user_id, world_id)` lookup path; no schema change was necessary. Functional tests passed on SQLite and disposable PostgreSQL 18. No performance benchmark was run; latency and E20 load gates remain unmeasured.

TERRA-012 route preview follow-up — 2026-11-07

A binary-heap Dijkstra preview runs only when a saved favorite route is selected; it searches at most the 4,096 world cells present in the known-terrain map. This bounds the search domain, but no browser latency or performance benchmark has been run. E20 latency and load gates remain open.

## TERRA-011 conversion — 2026-11-07

The mixed SQLite/PostgreSQL 18 test suite completed in 713.01 seconds (225 passed, 1 skipped); this is test-suite wall time, not a production performance benchmark. The conversion reads known-world state and runs the existing terrain reachability search over at most 4,096 world cells before committing. No request-latency, concurrency-under-load or endurance benchmark was run. E20 performance gates remain open.

## TERRA-014 spawn selection — 2026-11-07

Genesis auto-selection filters candidate sectors against existing colony coordinates; the candidate scan is bounded by the existing finite world map (4,096 cells). The PostgreSQL 18 focused regression passed. No request-latency, spawn-saturation, concurrency-under-load, or endurance benchmark was run; E20 gates remain open.

## TERRA-013 alliance aggregation — 2026-11-07

Alliance aggregation scans the already loaded finite world outpost list and a single membership lookup when building the region snapshot; the cache key includes membership to avoid stale boundaries after joins/leaves. No performance benchmark or load test was run. E20 latency/load gates remain open.

## TERRA-003 starting progress — 2026-11-07

Starting resources and level-1 production are constant-cost initialization; no runtime performance benchmark was run. Spawn terrain/neutral target fairness and E20 load/performance gates remain unmeasured.

TERRA-003 final adapter/full-suite follow-up (2026-11-07): 159 passed/76 skipped in 131.78s is test-run time only. No game request latency/capacity benchmark was performed; E20 gates remain open.

TERRA-001 generation regression (2026-11-07): full-suite wall time 144.48s is test runtime only. No generation latency or production load benchmark was conducted; E20 capacity gates remain open.

TERRA-002 race follow-up (2026-11-07): the two-player race regression is correctness coverage, not a throughput/concurrency capacity benchmark. E20 load gates remain open.

TERRA-004 multiworld follow-up (2026-11-07): focused Fog isolation check and full-suite wall time only; no map payload latency, browser rendering, or large-world query benchmark was run.

TERRA-005 adapter follow-up (2026-11-07): 16-region cap regression is correctness evidence only; no production throughput/latency benchmark was run.


ECO-006 (2026-11-07): Barrier-synchronized concurrent prerequisite regression verifies correctness only. The 141.69s full-suite duration is test runtime, not server performance. No latency, capacity or endurance benchmark was performed.


ECO-010 (2026-11-07): Market-history world-isolation regression is correctness evidence. Full-suite 129.12s is test runtime only; market query latency/scale and load remain unmeasured.


F2-004 (2026-11-07): CSRF resynchronization adds a state request and a single retry only after an explicit CSRF mismatch. No latency or load benchmark was run; full test runtime is not a service performance measurement.

OPS-016 heartbeat check regression measures correctness only. No health/readiness latency or failure-recovery load benchmark was run.

OPS-004/OPS-015 restore timing was not used as a capacity benchmark. No backup-duration, restore-throughput or 30-minute load measurement is claimed.


OPS-010 property regression update (2026-11-07): the full test suite took 181.49s on local SQLite and 819.00s on disposable PostgreSQL 18; these are test-suite runtimes, not service-performance measurements. No 30-minute gameplay load or capacity benchmark was run.


W10 NPC update (2026-11-07): the worker checks world settings each cycle and scans outposts only when a five-minute frontier interval elapses. Missed intervals are applied arithmetically and stock is capped at the existing tier capacity. Full SQLite test runtime 158.11s is not a service performance benchmark. No production latency/capacity or 30-minute endurance measurement was made.

W10 final local suite completed in 162.56s (172 passed/83 skipped); focused PostgreSQL 18 adapter case passed. Test-suite duration is not a request-latency or throughput metric. No endurance benchmark was run.

K03 scout arrival regressions (2026-11-07) are correctness checks only. Full SQLite suite runtime 162.50s is test runtime, not application throughput or service latency. No performance claim is made.

K07 recall tests are functional checks. Their runtime is not a service latency or throughput benchmark; no load/endurance performance claim is made.


K07 full SQLite regression runtime was 168.80s (180 passed/91 skipped). This is test-suite runtime only; no latency, throughput or 30-minute load measurement was run. Staging TLS issue remains an operational readiness gap.


K04/WAR-005 full SQLite suite completed in 175.15s (182 passed/92 skipped); this is test-suite runtime, not application latency or throughput. No load/endurance benchmark was run. Simulator performs one known-world post lookup and a pure battle calculation; no measured performance claim is made.

PostgreSQL 18 focused simulator correctness checks passed in a disposable no-volume container; no latency or throughput measurement was collected.


WAR-020 exercised 24,336 pure combat combinations within the regression test. This is correctness coverage, not a latency/load result; full suite took 173.41s. No 30-minute endurance benchmark was run.

## 2026-11-07 continuation — K13

No performance benchmark or load claim was added. K13 profile listing is account-scoped, capped at ten rows per user and backed by an owner/order index. Full SQLite suite and focused PostgreSQL/API cases passed as recorded in RESUME_STATE.json. A 30-minute endurance/load run remains outstanding.

## 2026-11-07 — K08 workload scope

Expedition resolution uses a fixed number of SHA-256 digests per arriving job, independent of world size. No load or throughput claim is made. Full Python suite is pending at checkpoint; the 30-minute player lifecycle/load gate remains open.

## 2026-11-07 K08 checkpoint

Expedition outcome generation performs a fixed number of SHA-256 operations per mission and does not scale with world size. Restore drill runtime and full-suite duration are correctness/verification observations only. No gameplay request-latency, throughput, capacity or 30-minute endurance benchmark was run.

## 2026-11-07 K12 report update

Structured combat report generation adds bounded JSON for the current single FUR-2 round and an expandable client view. No performance benchmark was run. This correctness and rendering change does not establish request latency, throughput or load capacity.

WAR-016 arrival checks add no per-request loops or new persistence. Four adapter cases validate correctness, not runtime performance. No latency/load/endurance benchmark was run.

## T02 concurrency checkpoint — 2026-11-07

Added an eight-way concurrent worker-cycle regression for one due job; it asserts a single completion/report and no quarantine. Together with command/mission replay, concurrent double-spend and simulated worker crash rollback/retry tests, the targeted scenarios passed on SQLite and disposable PostgreSQL 18. This is correctness evidence, not a load result. No throughput, p95/p99, capacity, resource-utilization or 30-minute endurance benchmark was run; OPS-012 remains open.


## SOC-009 alliance bulletin query — 2026-11-07

The member feed uses the `(alliance_id, created DESC, id DESC)` index for ordered keyset access. State and cursor endpoint cap each page at 100 records; archived and active records use the same stable ordering. The cursor endpoint rechecks current membership and binds the cursor to the same alliance. Focused SQLite and disposable PostgreSQL 18 migration/domain/API cases pass. No load or memory benchmark was run, and large-alliance/load readiness is not claimed.

## E09 SOC-008 alliance forum — 2026-11-07

Correctness tests cover 50-thread paging, at most 100 posts per thread and cursor retrieval for older threads. No latency, query-plan, concurrency-under-load, throughput or memory benchmark was run. E20 capacity and endurance gates remain open.

## E09 SOC-004 diplomacy chronicle — 2026-11-07

The public state query uses a descending timestamp/ID index and a 100-row limit. Correctness tests pass on SQLite and disposable PostgreSQL 18. No query-plan, latency, load, or endurance measurement was made; E20 performance gates remain open.


## 2026-11-08 — Begrenzung der Imperiumslisten

Der `/api/v1/state`-Payload enthält höchstens 50 Welteinträge und 50 Kolonien im globalen Imperiumsverzeichnis. Zusätzlich bleibt die kleine, regelgebundene Kolonieliste der aktiven Welt vollständig für Karte und Versorgung verfügbar (maximal vier nach Spielregeln; Abfrage defensiv auf fünf begrenzt). Weitere Imperiumseinträge werden über keyset-paginierte Endpunkte geladen. Die aktive-Welt-Kolonieslotanzahl wird per `COUNT(*)` abgefragt. API- und Adapterregressionen bestätigen Seitenlimit, Cursorfortschritt und Besitzprüfung. Es wurde kein Last- oder Durchsatzwert gemessen; dies ist kein Benchmark und ersetzt den weiterhin offenen 30-Minuten-Lasttest nicht.
