# blacksmith-test

An objective, reproducible comparison of [Blacksmith](https://blacksmith.sh) CI runners vs. GitHub-hosted GitHub Actions runners — measuring performance, reliability, and developer experience using [Immich](https://github.com/immich-app/immich) as a realistic, large-scale test workload.

This is a personal engineering project, kept separate from any employer's codebase.

## Why Immich

Immich is a large, actively developed self-hosted photo/video management app with a real-world CI surface: a NestJS server, a SvelteKit web client, a Dart/Flutter mobile app, Python-based machine-learning services, and a Docker-Compose-based end-to-end test suite. That mix of unit tests, integration tests, linting, and multi-service Docker builds makes it a good stand-in for a typical production monorepo — much more representative than a synthetic "hello world" benchmark.

## Repositories

- **Test-subject fork:** [github.com/mejoff/immich](https://github.com/mejoff/immich) — a real GitHub fork of [github.com/immich-app/immich](https://github.com/immich-app/immich) (kept linked to upstream for syncing), with two long-lived benchmark branches layered on top.
- **This repo:** the benchmark harness — normalization patch, timing-collection scripts, raw results, and the results-comparison site.

## Methodology

1. **Common base.** A `bench-base` tag on the immich fork marks the commit both benchmark branches derive from.
2. **Normalization patch.** Immich's upstream CI includes org-only plumbing that only works inside the `immich-app` GitHub org — a custom GitHub App token step and a private self-hosted runner label. A normalization patch strips both so the workflows run unmodified on a personal fork.
3. **Two long-lived branches**, both branched from `bench-base`:
   - `bench/gha` — CI jobs run on GitHub-hosted `ubuntu-latest` runners.
   - `bench/blacksmith` — the same jobs run on Blacksmith's `blacksmith-4vcpu-ubuntu-2404` runners.
4. **Benchmarked jobs** (mirrored identically on both branches):
   - Server unit tests
   - Server "medium" tests
   - Web unit tests + lint
   - Docker-Compose-based e2e suite
   - Immich server + machine-learning (CPU) Docker image builds

## Results

Timing data is pulled via the GitHub Actions API (`gh api repos/mejoff/immich/actions/runs` and `.../jobs`) and written to [`results/`](results/) as CSV, one row per CI run:

```
platform, workflow, job, cache_state, queue_s, job_duration_s, run_total_s, conclusion
```

The comparison is visualized as a static site in [`site/`](site/) (in progress — see [`explorations/`](explorations/) for design mockups landing there first).

## Layout

```
results/       CSV output, one row per CI run
scripts/       data-collection scripts (GitHub Actions API -> CSV)
site/          results-comparison webpage
explorations/  design mockups, promoted to site/ once finalized
immich/        (gitignored) nested plain clone of the immich fork, its own git history/remotes
```
