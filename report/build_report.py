# Rebuilds report/blacksmith-vs-github-actions-report.pdf
# Sources: results/pilot-notes.md + results/pilot-results.csv
# Layout transcribed from the original ReportLab render (letter, 612x792),
# with the 2026-07-08 styling revision pass applied:
#   - no left accent bars on any callout box
#   - masthead/kicker orange deepened #ff8200 -> #d96d0c (only surviving orange)
#   - TL;DR box: light blue bg, body 9.5 -> 11.5pt
#   - p2 "wasn't flawless" callout body halved; agents-section opener reworded
#   - p3 chart: thicker bars, Blacksmith hunter green, GHA dove gray (slate),
#     speedup tags + table Speedup column hunter green; ESLint box light green
#   - p4 heading "My real worry" -> "A concern", concern box neutral gray +
#     body halved; scorecard Call column all black
#
# Run: uv run --with reportlab python3 build_report.py

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

W, H = letter  # 612 x 792

# ---------------------------------------------------------------- palette
PAPER = "#f9f7f3"
INK = "#262626"
GRAY = "#5d5d5d"
LIGHT = "#939393"
RULE_LIGHT = "#c9c9c9"
RULE_ROW = "#dadbdc"
DEEP_ORANGE = "#d96d0c"   # replaces #ff8200 masthead/kicker/accents
HUNTER = "#355e3b"        # Blacksmith bars / speedup tags / table speedups
DOVE = "#6f7277"          # GHA bars (Menlo slate)
TLDR_BG = "#eaf1fb"       # was cream #fbf0e7
CITRON_BG = "#fbfae4"     # unchanged
GREEN_BG = "#eaf3ea"      # ESLint box, was #fbf0e7
CONCERN_BG = "#efeeea"    # was pale mist #f1f9f9
BLACK = "#000000"

HV, HB, TB, CO, SY, HO = ("Helvetica", "Helvetica-Bold", "Times-Bold",
                          "Courier", "Symbol", "Helvetica-Oblique")

EM, EN, RSQ, LDQ, RDQ, MID, BUL, ARR = ("—", "–", "’",
                                        "“", "”", "·",
                                        "•", "→")

MX = 67.2          # body text left margin
BOXW = 477.6       # callout box width
BODY = 9.5
LEAD = 13.5


# ---------------------------------------------------------------- helpers
def r(t, f=HV, s=BODY, col=INK):
    return (t, f, s, col)


def code(t, s=8.5):
    return (t, CO, s, INK)


def runs_w(runs):
    return sum(stringWidth(t, f, s) for t, f, s, _ in runs)


def draw_runs(c, x, y, runs):
    for t, f, s, col in runs:
        c.setFillColor(col)
        c.setFont(f, s)
        c.drawString(x, y, t)
        x += stringWidth(t, f, s)


def wrap_runs(runs, width):
    """Greedy word wrap over styled runs -> list of line run-lists."""
    words = []  # each: (list_of_fragments, width, trailing_space_w)
    cur, curw = [], 0.0
    for t, f, s, col in runs:
        parts = t.split(" ")
        for i, p in enumerate(parts):
            if p:
                cur.append((p, f, s, col))
                curw += stringWidth(p, f, s)
            if i < len(parts) - 1:  # a space followed this part
                words.append((cur, curw, stringWidth(" ", f, s), (f, s, col)))
                cur, curw = [], 0.0
    if cur:
        words.append((cur, curw, 0.0, None))
    lines, line, linew = [], [], 0.0
    pend_sp = 0.0
    pend_style = None
    for frags, w, spw, style in words:
        add = (pend_sp if line else 0) + w
        if line and linew + add > width:
            lines.append(line)
            line, linew = [], 0.0
        if line and pend_style:
            f, s, col = pend_style
            line.append((" ", f, s, col))
            linew += pend_sp
        line.extend(frags)
        linew += w
        pend_sp, pend_style = spw, style
    if line:
        lines.append(line)
    return lines


def para(c, x, y, lines, lead=LEAD):
    """Draw pre-broken lines (each a run-list); return baseline of last line."""
    for ln in lines:
        draw_runs(c, x, y, ln if isinstance(ln, list) else [ln])
        y -= lead
    return y + lead


def bullet(c, x, y, lines, size=BODY, lead=LEAD, indent=11, bcol=DEEP_ORANGE):
    c.setFillColor(bcol)
    c.setFont(HB, size)
    c.drawString(x, y, BUL)
    return para(c, x + indent, y, lines, lead)


def callout(c, x, top, w, h, bg):
    c.setFillColor(bg)
    c.roundRect(x, top - h, w, h, 4, stroke=0, fill=1)
    # no left accent bar (removed everywhere in the 2026-07-08 revision)


def header(c, page):
    c.setStrokeColor(RULE_LIGHT)
    c.setLineWidth(0.6)
    c.line(61.2, 752.4, 550.8, 752.4)
    c.setFont(HB, 7)
    c.setFillColor(LIGHT)
    c.drawString(61.2, 759, "BLACKSMITH VS. GITHUB ACTIONS")
    c.setFillColor(DEEP_ORANGE)
    c.drawRightString(550.8, 759, "JOFF'S BENCHMARKING REPORT")
    c.setFont(HV, 7.5)
    c.setFillColor(LIGHT)
    c.drawString(61.2, 32.4, "July 2026")
    c.drawRightString(550.8, 32.4, str(page))


def paper(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def h1(c, y, text):
    c.setFillColor(INK)
    c.setFont(HB, 14.5)
    c.drawString(MX, y, text)


def h2(c, y, text):
    c.setFillColor(INK)
    c.setFont(HB, 10.5)
    c.drawString(MX, y, text)


# ---------------------------------------------------------------- page 1
def page1(c):
    paper(c)
    # masthead bar + kicker + underline: deep orange (was #ff8200)
    c.setFillColor(DEEP_ORANGE)
    c.rect(0, 781.92, 612, 10.08, stroke=0, fill=1)
    c.setFont(HB, 10)
    c.drawString(61.2, 684, "J O F F ' S   B E N C H M A R K I N G   R E P O R T")
    c.setStrokeColor(DEEP_ORANGE)
    c.setLineWidth(2)
    c.line(61.2, 672.48, 140.4, 672.48)

    c.setFillColor(INK)
    c.setFont(TB, 40)
    c.drawString(61.2, 627.84, "Blacksmith vs.")
    c.drawString(61.2, 586.08, "GitHub Actions")

    c.setFillColor(GRAY)
    c.setFont(HV, 12)
    c.drawString(61.2, 555.84, "Six real CI jobs from the Immich monorepo, run cold and warm on both")
    c.drawString(61.2, 539.28, f"platforms {EM} in one sitting, with a lot of help from agents.")

    c.setFillColor(LIGHT)
    c.setFont(HV, 9.5)
    c.drawString(61.2, 516.24, f"Joff Redfern  {MID}  July 2026  {MID}  a personal pilot, not a powered study")

    c.setFont(HV, 7.5)
    c.drawString(61.2, 32.4, f"Data: results/pilot-results.csv  {MID}  Notes: results/pilot-notes.md  {MID}  Repo: Wanderment-Farms/immich")

    # ---- TL;DR box: light blue bg, no bar, body bumped 9.5 -> 11.5pt
    BS, BL = 11.5, 15.5
    tw = BOXW - 28 - 12
    bullets = [
        [r("Blacksmith was faster on "), r("every one of the six jobs", HB, BS),
         r(f" I tested {EM} "), r("1.4x to 5.3x", HB, BS),
         r(f". The standout is ESLint: ~5.3x faster (390{EN}444s on GitHub Actions vs 73{EN}101s on Blacksmith), and it held across three runs.")],
        [r("Reliability was a genuine tie: "),
         r("0 platform failures in 14 job-runs on each side", HB, BS), r(".")],
        [r(f"The setup friction is real {EM} a GitHub org, an overnight approval, workflow edits {EM} but it{RSQ}s a "),
         r("one-time tax", HB, BS),
         r(" on a tool that then pays out on every CI run.")],
        [r(f"What actually worries me isn{RSQ}t the product. It{RSQ}s that "),
         r(f"Blacksmith is invisible to the engineers it{RSQ}s helping", HB, BS),
         r(f" {EM} everything surfaces through GitHub{RSQ}s UI, and a tool nobody can see is a tool a budget review can cut without knowing what it does.")],
        [r(f"Honest caveat: n=1{EN}2 per cell. This is a real pilot, directional {EM} not a statistically powered study.")],
    ]
    bullets = [[(t, f, BS, col) for t, f, _, col in b] for b in bullets]
    wrapped = [wrap_runs(b, tw) for b in bullets]
    nlines = sum(len(wr) for wr in wrapped)
    top = 454.8
    box_h = 20 + 15 + (nlines - 1) * BL + 14
    callout(c, MX, top, BOXW, box_h, TLDR_BG)
    c.setFillColor(INK)
    c.setFont(HB, 10)
    c.drawString(MX + 14, top - 20, "TL;DR")
    y = top - 20 - 15
    for wr in wrapped:
        bullet(c, MX + 14, y, wr, size=BS, lead=BL, indent=12)
        y -= len(wr) * BL


# ---------------------------------------------------------------- page 2
def page2(c):
    paper(c)
    header(c, 2)
    h1(c, 713.9, "How I picked the benchmark")
    para(c, MX, 695.9, [
        [r(f"I didn{RSQ}t want a toy repo. I set the evaluation criteria first: real Docker builds, a real test suite, linting, dependency")],
        [r("caching, multiple parallel CI jobs, and enough complexity to actually stress both platforms. Then I had my coding")],
        [r("agent vet candidate open-source repos against that list before I committed to one. We landed on")],
        [r("immich-app/immich", HB), r(f" {EM} a mature, actively-maintained self-hosted photo-management app with a real TypeScript")],
        [r("monorepo, Docker multi-arch builds, Postgres integration tests, and a Svelte web frontend. It checks every box,")],
        [r("and its CI is heavy enough that runner performance actually matters.")],
    ])
    para(c, MX, 607.9, [
        [r(f"The setup: I forked Immich into a fresh org and ran the same six jobs on two branches {EM} "), code("bench/gha"), r(" on stock")],
        [r("GitHub-hosted runners, "), code("bench/blacksmith"), r(f" on Blacksmith {EM} each cold-cache and warm-cache. One honest")],
        [r(f"scope note: Immich{RSQ}s real CI depends on an org-only GitHub App token and self-hosted runner labels, so I wrote a")],
        [r("minimal from-scratch workflow (~70 lines) rather than porting their "), code("test.yml"), r(" line-by-line. That means this")],
        [r(f"measures runner performance well, but it isn{RSQ}t a dress rehearsal for migrating an existing workflow. And again:")],
        [r(f"n=1{EN}2 runs per cell. Directional, not p95-grade.")],
    ])
    h1(c, 507.9, "How it actually got done: eight agents in one sitting")

    # Reworded opener (dropped the "part I most want colleagues to notice" framing)
    opener = wrap_runs([
        r("Honestly, this is the biggest reason the whole thing got done in an evening instead of a week: over the course of the pilot I forked off "),
        r("eight separate agents", HB),
        r(", each with a focused job, while the main thread handled all the actual git and CI orchestration directly:"),
    ], 483.6)
    last = para(c, MX, 489.9, opener)

    y = last - 20.5
    last = bullet(c, MX, y, [[r("Two", HB), r(f" to stand up the infrastructure {EM} forking and preparing the repos, and designing the results page.")]])
    last = bullet(c, MX, last - 17.5, [
        [r("Four running in parallel", HB), r(" to independently research and draft the workflow configs for the four heaviest CI jobs.")],
        [r(f"Each one read the real Immich source to figure out the right commands {EM} Postgres services, submodules,")],
        [r(f"build steps {EM} rather than guessing from the README.")],
    ])
    last = bullet(c, MX, last - 17.5, [[r("Two", HB), r(" successive passes writing this report itself.")]])
    last = para(c, MX, last - 21.5, [
        [r("The four parallel drafting agents are the interesting case: writing benchmark workflows for an unfamiliar")],
        [r("half-million-line monorepo is exactly the kind of work that serializes badly for one person. Fanned out, it happened")],
        [r(f"in roughly the time it takes to draft one. That{RSQ}s the point to land {EM} agent orchestration wasn{RSQ}t a garnish on this")],
        [r("project, it was the enabler.")],
    ])
    h2(c, last - 24.5, f"It wasn{RSQ}t flawless, and that{RSQ}s part of the story")

    # ---- callout: citron bg kept, bar removed, body cut to two sentences
    body = wrap_runs([
        r("One drafting agent defaulted the Docker build to "), code("push: true"),
        r(f" against a public GHCR registry {EM} a safety check caught it, and both branches were fixed to build-only. Separately, "),
        code("server-medium-tests"),
        r(" failed identically on both platforms until a one-line submodule fix ("),
        code("submodules: 'recursive'"),
        r(f") {EM} our bug, not a platform{RSQ}s, caught and fixed on both branches."),
    ], BOXW - 28)
    top = last - 24.5 - 6.5
    box_h = 19.5 + (len(body) - 1) * LEAD + 14
    callout(c, MX, top, BOXW, box_h, CITRON_BG)
    para(c, MX + 14, top - 19.5, body)


# ---------------------------------------------------------------- page 3
def page3(c):
    paper(c)
    header(c, 3)
    h1(c, 713.9, "Results: Blacksmith won every job")
    para(c, MX, 695.9, [
        [r(f"Same commit, same workflow logic, same jobs {EM} the only variable is the runner. Blacksmith was faster on all six,")],
        [r("from ~1.4x on the e2e suite to a 5.3x gap on the ESLint step. No job favored GitHub Actions.")],
    ])

    # ---- grouped bar chart (local origin 67.2, 479.4)
    ox, oy = 67.2, 479.4
    # legend: GHA dove gray, Blacksmith hunter green
    c.setFillColor(DOVE)
    c.rect(ox + 118, oy + 186, 8, 8, stroke=0, fill=1)
    c.setFillColor(GRAY)
    c.setFont(HV, 7.5)
    c.drawString(ox + 130, oy + 187, "GitHub Actions")
    c.setFillColor(HUNTER)
    c.rect(ox + 203, oy + 186, 8, 8, stroke=0, fill=1)
    c.setFillColor(GRAY)
    c.drawString(ox + 215, oy + 187, "Blacksmith")
    c.setFillColor(LIGHT)
    c.drawRightString(ox + 489.6, oy + 187, f"cold-cache duration, seconds  {MID}  tag = cold speedup")

    data = [
        ("server-unit-tests", 208, 88, "2.4x"),
        ("server-medium-tests", 231, 117, "2.0x"),
        ("web-lint", 444, 105, "4.2x"),
        ("web-unit-tests", 117, 64, "1.8x"),
        ("e2e-tests-server-cli", 467, 366, "1.3x"),
        ("docker-build-server", 437, 251, "1.7x"),
    ]
    k = 276.0904 / 467.0          # pt per second (same scale as original)
    BAR_H = 12                    # thicker bars (was 9)
    for i, (job, gha, bs, tag) in enumerate(data):
        sep = oy + 142.3333 - i * 27.66667
        c.setFillColor(INK)
        c.setFont(HV, 7.8)
        c.drawRightString(ox + 115, sep + 11.333, job)
        gy, by = sep + 14.4, sep + 1.6
        c.setFillColor(DOVE)
        c.rect(ox + 118, gy, gha * k, BAR_H, stroke=0, fill=1)
        c.setFillColor(HUNTER)
        c.rect(ox + 118, by, bs * k, BAR_H, stroke=0, fill=1)
        c.setFillColor(GRAY)
        c.setFont(HV, 7)
        c.drawString(ox + 118 + gha * k + 3, gy + 3.5, f"{gha}s")
        c.drawString(ox + 118 + bs * k + 3, by + 3.5, f"{bs}s")
        c.setFillColor(HUNTER)                       # speedup tags: hunter green
        c.setFont(HB, 7.5)
        c.drawRightString(ox + 489.6, sep + 11.333, tag)
        c.setStrokeColor(RULE_ROW)
        c.setLineWidth(0.4)
        c.line(ox + 118, sep, ox + 481.6, sep)
    c.setStrokeColor(RULE_LIGHT)
    c.setLineWidth(0.8)
    c.line(ox + 118, oy + 4, ox + 118, oy + 170)

    c.setFillColor(LIGHT)
    c.setFont(HV, 7.5)
    c.drawString(MX, 471.9, "Cold-cache runs shown; server-medium-tests uses the post-submodule-fix runs on both sides. Full cold+warm data: results/pilot-results.csv.")

    # ---- results table (local origin 61.2, 319.4)
    tx, ty = 61.2, 319.4
    cols = (2, 168.464, 285.968, 413.264)
    c.setFillColor(INK)
    c.setFont(HB, 8)
    for x, t in zip(cols, ("Job", "GHA (all runs)", "Blacksmith (all runs)", "Speedup")):
        c.drawString(tx + x, ty + 128, t)
    rows = [
        ("server-unit-tests", f"167{EN}208s", f"83{EN}101s", "~2.1x"),
        ("server-medium-tests", f"216{EN}231s", f"117{EN}122s", "~1.9x"),
        ("web-lint", f"417{EN}444s", f"99{EN}105s", "~4.2x"),
        ("web-unit-tests", f"117{EN}140s", f"61{EN}66s", "~2.0x"),
        ("e2e-tests-server-cli", f"467{EN}476s", f"290{EN}366s", f"~1.4{EN}1.6x"),
        ("docker-build-server (cold)", "437s", "251s", "~1.7x"),
    ]
    for i, (a, b, d, sp) in enumerate(rows):
        y = ty + 108 - i * 20
        c.setFillColor(GRAY)
        c.setFont(HV, 8)
        c.drawString(tx + cols[0], y, a)
        c.drawString(tx + cols[1], y, b)
        c.drawString(tx + cols[2], y, d)
        c.setFillColor(HUNTER)                       # speedups: hunter green
        c.setFont(HB, 8)
        c.drawString(tx + cols[3], y, sp)
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(tx, ty + 120, tx + 489.6, ty + 120)
    c.setStrokeColor(RULE_ROW)
    c.setLineWidth(0.4)
    for i in range(5):
        c.line(tx, ty + 100 - i * 20, tx + 489.6, ty + 100 - i * 20)

    # ---- ESLint standout callout: light green bg, no bar
    top = 310.4
    callout(c, MX, top, BOXW, 101, GREEN_BG)
    c.setFillColor(INK)
    c.setFont(HB, 10)
    c.drawString(MX + 14, top - 20, "The standout: ESLint, 5.3x")
    para(c, MX + 14, 277.4, [
        [r(f"The {LDQ}Run linter{RDQ} step alone took "), r("390s on GitHub Actions vs 73s on Blacksmith", HB), r(f" {EM} 5.3x, far beyond the")],
        [r("~2x pattern everywhere else, and it held across all three runs (444/435/417s vs 105/99/101s total job time),")],
        [r(f"so it{RSQ}s not a cache artifact. It makes sense: ESLint{RSQ}s TypeScript-aware rules are largely single-threaded,")],
        [r(f"CPU-bound work {EM} exactly the profile where Blacksmith{RSQ}s bare-metal single-core-performance claim should")],
        [r("show its biggest gains, and it did.")],
    ])

    h2(c, 180.9, f"Where they didn{RSQ}t differ")
    para(c, MX, 164.9, [
        [r("Docker layer caching is a wash.", HB), r(" Warm rebuilds went 437s"), (ARR, SY, BODY, INK), r("18s on GHA and 251s"), (ARR, SY, BODY, INK), r(f"17s on Blacksmith {EM} both")],
        [r("effectively instant when nothing changed. "), r("Reliability is a genuine tie:", HB), r(" 14 job-runs attempted per platform, one")],
        [r(f"failure each {EM} and it was the "), r("same", HO), r(" failure, my own submodule bug, fixed identically on both sides. No flakiness,")],
        [r(f"no cache corruption, no run that queued and never started. Fair warning: 14 runs says {LDQ}no flakiness observed,{RDQ}")],
        [r(f"not {LDQ}provably equally reliable{RDQ} {EM} real flake-hunting needs 20{EN}30 runs per cell. And since Blacksmith is a runner")],
        [r(f"substitution, not a different CI product, day-to-day debugging {EM} logs, per-step timing, failure reporting {EM} is")],
        [r("literally the same GitHub Actions UI on both (verified with a deliberate broken-assertion push to each branch:")],
        [r("identical Vitest output).")],
    ])


# ---------------------------------------------------------------- page 4
def page4(c):
    paper(c)
    header(c, 4)
    h1(c, 713.9, f"The setup tax is real {EM} and one-time")
    para(c, MX, 695.9, [
        [r("Getting Blacksmith running took real effort that GitHub Actions never asks for: its signup requires the repo to be")],
        [r("owned by a GitHub "), r("organization", HO), r(" (I had to transfer both repos out of my personal account mid-experiment, which")],
        [r(f"auto-cancelled two queued runs), there was an overnight wait for Blacksmith{RSQ}s human approval of the App install")],
        [r(f"{EM} the single biggest source of dead time in the whole session {EM} and then a workflow-editing pass to swap runner")],
        [r("labels and cache actions. Their docs also never mention the org requirement, and their Migration Wizard defaults")],
        [r(f"to auto-rewriting every workflow in the repo {EM} fine for a real migration, actively wrong for a controlled comparison.")],
    ])
    para(c, MX, 607.9, [
        [r(f"But I{RSQ}ve come around on how much this should count against them. Every bit of that friction is "), r("paid once", HB), r(". For a")],
        [r(f"large engineering org, it{RSQ}s an afternoon plus one approval wait {EM} and then it just runs, with near-zero")],
        [r(f"maintenance, delivering the speedup on every CI run afterward. It{RSQ}s hard to hold a one-time tax against a tool with")],
        [r(f"a permanent dividend. GitHub Actions still wins the {LDQ}time to first green build{RDQ} race, clearly. It just doesn{RSQ}t matter")],
        [r("much by week two.")],
    ])
    # toned-down heading ("My real worry" -> "A concern")
    h1(c, 521.4, f"A concern: Blacksmith is invisible to the people it{RSQ}s helping")

    # ---- concern box: neutral gray bg, no bar, body halved to one paragraph
    body = wrap_runs([
        r(f"At no point in this pilot did {LDQ}Blacksmith{RDQ} surface to a working engineer {EM} every run, log, and green check lives in the normal GitHub Actions UI, and nobody gets told why the build got faster. Here{RSQ}s the concrete failure mode: eighteen months from now, someone in finance runs a {LDQ}what tools do we actually still need{RDQ} audit and finds a Blacksmith line item nobody on the team can explain {EM} so it gets cut, CI quietly gets 2{EN}5x slower, and nobody connects the two for a quarter. A product whose entire value is invisible-by-design has to work harder to stay legible to the org paying for it."),
    ], BOXW - 28)
    top = 512.9
    box_h = 19.5 + (len(body) - 1) * LEAD + 14
    callout(c, MX, top, BOXW, box_h, CONCERN_BG)
    para(c, MX + 14, top - 19.5, body)

    # ---- scorecard (reflowed up under the shorter box)
    sc_title = top - box_h - 31
    h1(c, sc_title + 2.5, "Scorecard")
    tx, ty = 61.2, sc_title - 127.5
    cols = (2, 109.712, 403.472)
    c.setFillColor(INK)
    c.setFont(HB, 8)
    for x, t in zip(cols, ("Dimension", "Read", "Call")):
        c.drawString(tx + x, ty + 109.5, t)
    rows = [
        (91, "Performance", ["1.4–5.3x faster on all six jobs; biggest edge on CPU-bound lint"], "Blacksmith"),
        (72.5, "Reliability", ["0 platform failures in 14 job-runs per side; no flakiness observed"], "Tie"),
        (54, "Setup & onboarding", ["GHA is zero-setup; Blacksmith's org + approval + edits is a real but one-time tax"], "GHA, narrowly"),
        (35.5, "Observability", ["Identical logs/UI (same GHA under the hood); Blacksmith advertises SSH debug,", "untested"], "Tie"),
        (6.5, "Legibility to the org", [f"Blacksmith never surfaces to the engineers it helps {EM} budget-cut exposure"], "My open worry"),
    ]
    for y, dim, read, call in rows:
        c.setFillColor(BLACK)
        c.setFont(HB, 8)
        c.drawString(tx + cols[0], ty + y, dim)
        c.setFillColor(GRAY)
        c.setFont(HV, 8)
        for j, ln in enumerate(read):
            c.drawString(tx + cols[1], ty + y - j * 10.5, ln)
        c.setFillColor(BLACK)                 # Call column: plain black, no color-coding
        c.setFont(HB, 8)
        c.drawString(tx + cols[2], ty + y, call)
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(tx, ty + 103, tx + 489.6, ty + 103)
    c.setStrokeColor(RULE_ROW)
    c.setLineWidth(0.4)
    for yy in (84.5, 66, 47.5, 18.5):
        c.line(tx, ty + yy, tx + 489.6, ty + yy)

    bl_title = ty - 35
    h2(c, bl_title + 2.5, "Bottom line")
    para(c, MX, bl_title - 44.5 + 31, [
        [r("The speed is real, consistent, and biggest exactly where the physics say it should be. The reliability gap is zero at")],
        [r(f"this sample size. The setup tax is real but amortizes to nothing. If I were running a big CI bill, I{RSQ}d take the trade {EM}")],
        [r(f"and then I{RSQ}d make sure my team actually knew Blacksmith existed, because the product won{RSQ}t tell them.")],
    ])


# ---------------------------------------------------------------- build
def main():
    out = "/Users/joffredfern/blacksmith-test/report/blacksmith-vs-github-actions-report.pdf"
    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(f"Blacksmith vs. GitHub Actions {EM} Joff's Benchmarking Report")
    c.setAuthor("Joff Redfern")
    for fn in (page1, page2, page3, page4):
        fn(c)
        c.showPage()
    c.save()
    print("wrote", out)


if __name__ == "__main__":
    main()
