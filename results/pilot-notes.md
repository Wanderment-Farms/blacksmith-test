# Pilot run notes — 2026-07-08 (time-boxed, <1hr)

This is the tonight's-pilot version of the study, not the full statistically-powered
benchmark. Scope: 1 job (`server-unit-tests`), n=1 cold + n=1 warm per platform.
No Docker/e2e/mobile jobs tonight — deferred to the full run. Numbers here are
directional, not p50/p95-grade.

## Setup & Onboarding (real, timestamped)

- **Elapsed time, first workflow commit -> now:** ~40 min (2026-07-08T02:48:50Z ->
  2026-07-08T03:28:29Z). Covers writing a minimal `bench.yml`, two debugging
  detours below, and an unplanned repo-ownership transfer.
- **Workflow lines changed:** +70 lines, one new file (`bench.yml`), bench-base -> bench/gha.
  Caveat: this is a from-scratch minimal workflow, not a line-by-line trim of Immich's
  real `test.yml` -- not representative of a true "migrate the existing workflow" effort.
  The full run should redo this properly.
- **Issues hit:**
  1. Immich's real CI depends on an org-only GitHub App token + self-hosted runner
     labels (`mich`, `pokedex-large`) -- not portable to a fork. Known going in.
  2. `//:plugins` unexpectedly required the `extism-js` WASM toolchain via
     `plugin-core`, which the server doesn't actually depend on -- dropped it from
     the install/build scope.
  3. GitHub won't let `workflow_dispatch`-only workflows be dispatched unless the
     file exists on the repo's default branch. Fixed by adding a `push` trigger
     scoped to each bench branch instead of touching `main` (a safety classifier
     correctly blocked the first attempt to push workflow changes to `main`).
  4. Blacksmith's signup requires the target repo to be owned by a GitHub
     organization -- required transferring both repos from `mejoff` to a new org
     (`Wanderment-Farms`) mid-experiment. Side effect: the transfer auto-cancelled
     the two already-queued Blacksmith runs; they needed re-triggering.

## Workflow Performance (real, GitHub Actions side only so far)

| cache state | queue_s | job_duration_s |
|---|---|---|
| cold | 2 | 208 (3m28s) |
| warm (rerun) | 1 | 200 (3m20s) |

Only ~8s faster warm vs cold (n=1 each, not statistically meaningful). Likely
explanation: this job is dominated by compute-bound steps (lint, tsc, vitest),
not the dependency-install step that caching actually speeds up.

Blacksmith side: pending -- App authorization in progress as of this note.

## Observability & Debugging

Deliberate failure pushed to `bench/gha` (flipped one assertion in
`server/src/utils/mime-types.spec.ts`, commit `2b3bb6e2f`) to capture the
debugging experience. GitHub Actions side result below; Blacksmith side to
follow once its runs are live.
