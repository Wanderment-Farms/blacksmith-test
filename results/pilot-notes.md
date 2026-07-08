# Pilot run notes — 2026-07-08

Started as a time-boxed <1hr pilot (1 job, n=1 cold+warm per platform), then
expanded same-session to all 6 planned benchmark jobs once Blacksmith access
came through. Still not the full 20-30-runs-per-cell statistically-powered
study from the original plan — this is n=1-2 per cell, directional not
p50/p95-grade — but now covers the full job matrix instead of just one job.

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

Blacksmith side: see full 6-job expansion below (this dimension's first
n=1 comparison, 88s cold / 101s warm, is superseded by the fuller data there).

## Full 6-job suite expansion (2026-07-08, later same session)

Once Blacksmith access came through, drafted the remaining 5 jobs
(`server-medium-tests`, `web-lint`, `web-unit-tests`, `e2e-tests-server-cli`,
`docker-build-server`) via 4 parallel research agents, each investigating the
real Immich source to find the right commands rather than guessing. Findings
and real cold+warm data for all 6 jobs are in `results/pilot-results.csv`.

**Caught before it shipped:** one drafting agent defaulted the Docker build job
to `push: true` against `ghcr.io/wanderment-farms/immich-server` -- a real
public artifact nobody asked for. A safety check blocked it on the Blacksmith
branch before it landed; the GitHub Actions branch had already started pushing
when caught, so that in-flight run was cancelled mid-push (its push step shows
`cancelled`, not `success`). Both branches fixed to build-only (`push: false`).

**Real bug found and fixed:** `server-medium-tests` failed identically on both
platforms with every EXIF-derived test returning the same fallback date and
empty tag arrays. Root cause: `server/test/medium.factory`'s `testAssetsDir`
resolves into `e2e/test-assets`, a git submodule (`immich-app/test-assets`) --
our checkout step wasn't fetching submodules for that job. One-line fix
(`submodules: 'recursive'`) on both branches resolved it completely.

**Standout finding -- ESLint is where Blacksmith's edge is biggest so far:**
the `web-lint` job's "Run linter" step alone: **390s on GitHub Actions vs 73s
on Blacksmith -- a 5.3x difference**, far larger than the ~2x pattern seen on
every other job (server-unit-tests, e2e, etc.), and consistent across both the
cold and warm run (444s/435s GHA vs 105s/99s Blacksmith total job time, so
it's not a cache artifact). ESLint's TypeScript-aware rules are largely
single-threaded, CPU-bound work -- exactly the profile Blacksmith's
bare-metal/single-core-performance claim would predict showing its largest
gains on. Worth calling out explicitly in the final report as the most
platform-differentiated single step found, not just folded into an average.

**Docker layer caching, both platforms:** cold-to-warm went 437s->18s on GHA
(`type=gha` cache) and 251s->17s on Blacksmith (auto NVMe cache) -- both
essentially instant on a no-source-change rebuild. This one doesn't
differentiate the platforms; both caching approaches work equally well here.

**All 6 jobs, cold vs warm, both platforms (n=1-2 per cell, job_duration_s):**

| job | GHA cold | GHA warm | Blacksmith cold | Blacksmith warm |
|---|---|---|---|---|
| server-unit-tests | 167-208 | 200-205 | 88-99 | 83-101 |
| server-medium-tests | 209 (failed pre-fix) | 231 | 87 (failed pre-fix) | 117 |
| web-lint | 444 | 435 | 105 | 99 |
| web-unit-tests | 117 | 140 | 64 | 61 |
| e2e-tests-server-cli | 467 | 474 | 366 | 290 |
| docker-build-server | 437 | 18 | 251 | 17 |

## Observability & Debugging

Deliberate failure pushed to `bench/gha` (flipped one assertion in
`server/src/utils/mime-types.spec.ts`, commit `2b3bb6e2f`) to capture the
debugging experience. Same change pushed to `bench/blacksmith` (commit
`410c65d00`), queued and ready to fire the moment its runner connects.

**GitHub Actions result** (run 28915304177, [log](https://github.com/Wanderment-Farms/immich/actions/runs/28915304177)):
- Log clarity: excellent out of the box. Vitest's own reporter prints the exact
  file:line, an inline code snippet around the failing assertion, and a clean
  expected/received diff (`Expected: ".pngx"` / `Received: ".png"`) directly in
  the raw Actions log -- no extra tooling needed to spot the failing line.
- Time-to-signal: total run was 3m29s (created_at -> updated_at), effectively the
  same as a passing run. Our step ordering (format -> lint -> typecheck -> full
  test suite) has no fail-fast between steps, and Vitest itself ran the complete
  2237-test suite before reporting the one failure at the end -- so "the assertion
  I broke" and "20 unrelated tests I didn't touch" surface at the same time, same
  place. Worth noting for the full run: a job design choice (this one, inherited
  loosely from Immich's own `ci-unit` task), not a GitHub Actions platform limit.
- Per-step timing breakdown: visible natively (each step shows its own duration
  in the Actions UI/log) -- no extra tooling needed.
- SSH-into-runner debugging: not available natively; would need a marketplace
  action (e.g. `mxschmitt/action-tmate`) added to the workflow ahead of time.
- Cache hit/miss visibility: `actions/setup-node`'s cache step logs a clear
  "Cache restored from key: ..." / "Cache not found for input keys: ..." line.

**Blacksmith result** (run 28920794296, [log](https://github.com/Wanderment-Farms/immich/actions/runs/28920794296), redone fresh on 2026-07-08 morning after the App connected):
- Log clarity: identical to GHA -- same Vitest reporter, same exact file:line +
  inline diff. Makes sense: the log content is produced by Vitest running on the
  runner, not by the platform, so this dimension is essentially a wash between
  the two. Not a Blacksmith-specific finding, but worth stating plainly rather
  than assuming a "faster platform" also means "better logs" -- it doesn't
  follow, and here it genuinely doesn't differ.
- Time-to-signal: 88s job duration -- same as this run's own cold pass earlier,
  consistent with the GHA finding that one failing assertion doesn't shorten a
  no-fail-fast suite. Proportionally faster in wall-clock terms only because the
  whole job is faster on Blacksmith, not because failures surface sooner.
- Per-step timing: same native visibility, same UI, since these are still
  standard GitHub Actions runs (Blacksmith is a runner substitution, not a
  different CI product/UI).
- SSH-into-runner debugging: Blacksmith's own dashboard advertises this as a
  first-class feature (per their docs) -- did not test it directly tonight, but
  it's a real asymmetry against GHA's lack of a native equivalent (GHA needs a
  marketplace action like `mxschmitt/action-tmate`).
- Cache hit/miss visibility: `useblacksmith/cache`'s log output was less
  chatty than `actions/setup-node`'s built-in cache step -- didn't print an
  obvious "restored from key" / "not found" line in the same way. Worth a
  closer look if this dimension matters a lot to the final writeup.

**Net finding for this dimension:** the debugging experience itself (log
clarity, per-step timing) is essentially identical between the two platforms,
because both are still GitHub Actions runs under the hood -- Blacksmith's
differentiation here is entirely in speed and (per their docs, untested by us)
native SSH access, not in how failures are reported.

## Session paused overnight (2026-07-08, ~04:40 UTC)

Blacksmith support hasn't approved the GitHub App yet; expected tomorrow morning.
Picking back up: nothing to redo, everything is parked clean.

**State left behind:**
- Both repos live under the `Wanderment-Farms` org (transferred from `mejoff`
  mid-session -- Blacksmith signup requires org ownership).
- `bench/gha`: clean, passing, reverted after the deliberate-failure test. Real
  cold (208s) + warm (200s) data captured above.
- `bench/blacksmith`: clean, reverted, one fresh queued run (`28917954313`)
  waiting for a runner -- will fire the instant the App connects. This will be
  the first real Blacksmith data point (treat as the cold run).
- The stale broken-assertion run that had been sitting queued for over an hour
  was explicitly cancelled (`gh run cancel 28915362085`) so tomorrow's first
  Blacksmith run isn't a confusing intentional failure.

**Tomorrow's sequence once the App is approved:**
1. Confirm the queued run (`28917954313`) picks up and completes -- that's
   Blacksmith cold.
2. `gh run rerun 28917954313` for the warm-cache data point.
3. Redo the deliberate-failure test fresh on `bench/blacksmith` (same edit as
   `bench/gha`'s, `server/src/utils/mime-types.spec.ts` line 109 -> `.pngx`),
   capture the debugging-experience findings, then revert.
4. Decide: wrap up with this pilot's n=1 data as-is, or spend more time running
   the full 20-30-run matrix from the original plan before writing the report.
