# Terra feature gap matrix — source-level assessment

Status means verified in the isolated local source and tests, not in the running beta.

| Capability | Current FUR source | Terra MMORTS gap | Next gate |
| --- | --- | --- | --- |
| Accounts and persistent colonies | Implemented with session and colony state | Live compatibility and restore rehearsal | P0/P1 |
| World and fog | 64×64 seeded terrain, observed sectors and world-scoped outposts | Chunks/deltas, shared vision policy, two-client UI acceptance | P2/P3 |
| Map UI | Existing selectable grid, bookmarks and known-sector route overlay; this branch adds a fog-filtered minimap with mouse and keyboard navigation | Camera, zoom and direct group selection need product acceptance; manual device/accessibility review remains open | P3 |
| Economy/build/research | Server-owned resources, ledger, queues and versioned rules | Load and balance validation for direct-control economy | P4 |
| Pathfinding | Weighted four-neighbor travel cost; water blocked | Persisted path and group position, reroute/collision rules | P5 |
| Land units | Three FUR-2 types and provisional FUR-3 roster | Independent unit/group instances, HP, fuel, order queue | P5 |
| Combat and capture | Arrival-based PvE/PvP battle and outpost capture | Continuous targeting/damage, simultaneous capture race and replay | P6 |
| Multiplayer/social | Alliances, diplomacy, chat, trade and world events | Cross-world scope audit, live state synchronization and reconnection | P7 |
| Operations | Worker, health checks, Compose, backup scripts | Verified VPS inventory, PostgreSQL restore, load/SLO evidence | P0/P11 |

Delta Wars is visual/mechanical inspiration only. Its code, assets, names and balance values are not FUR inputs. The attached minimap illustrates categories and orientation; FUR needs original symbols and player-scoped visibility.
