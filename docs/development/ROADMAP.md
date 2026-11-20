# Development-system roadmap

1. Establish the root application in the authorized GitHub repository and require CI on pull
   requests.
2. Install the isolated `/opt/fur-empire-development` workspace and unprivileged `furdev` account.
3. Install and authenticate Codex using an officially supported flow; keep credentials readable
   only by `furdev`.
4. Run a no-product-change smoke task through queue, worker, log and persisted result.
5. Prove interrupted-task recovery and bounded retry behavior.
6. Add staging-only validation and a pull-request creation step; production release remains a
   separately approved operator action.
7. Import executable work from the existing implementation matrix and backlog after reconciling
   their status with current tests.

Parallel workers, Discord control and an MCP server are deferred until a measured need exists.
