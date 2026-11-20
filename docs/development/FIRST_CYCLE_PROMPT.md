# First controlled development-cycle task

This is an infrastructure acceptance task, not a gameplay change.

1. Read the repository `AGENTS.md` and the development-system documentation.
2. Verify that the checkout is an isolated `agent/task-*` worktree and that production paths are
   unavailable from this task.
3. Create `docs/development/CYCLE_PROOF.md` with the current UTC time, checked-out branch and commit,
   the validations you ran, and a concise statement that no gameplay or production state changed.
4. Run the focused development-runner tests.
5. Do not modify gameplay code, deployment secrets, production configuration or player data.

Stop after the evidence file and focused validation are complete. The runner will perform its own
post-validation, commit and branch publication.
