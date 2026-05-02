# Retrospect: 015-scanner-exclude-venv-dirs

## Workflow Summary

| Stage | Iterations | Verdict trail | Notes |
|-------|-----------|---------------|-------|
| Specification | 2 | REVISE → APPROVE | Iter1 had 2 BLOCKING (NFR-1 prescriptive impl-strategy language; AC-4 internal contradiction). Iter2 fixed both. |
| Clarification | 2 | REVISE → APPROVE | Iter1 had 2 BLOCKING + 1 WARNING (clarifications/spec mismatch on "in this order" frozenset claim; predicate-ordering tweak over-specifying impl detail; missing OOS-7 for symlinks). Iter2 reconciled. |
| Planning | 1 | APPROVE | Two NOTE-level suggestions (manual T5 vs automated test; `set` vs `any()` perf), both deferred per spec/clarification scope. |
| Task breakdown | 1 | APPROVE | All paths and tools cross-checked; "Plan corrections required" section emitted with `None`. |
| Implementation | 5 tasks × 1 iter each | 5× APPROVE | T1 (scanner.py edit), T2 (test file), T3 (unittest run, 307 pass), T4 (basedpyright clean), T5 (manual AC-2 sanity). |
| Validation | 1 | APPROVE | 26 PASS / 0 FAIL / 0 DEFERRED. |
| **Total** | **13 cycles** | **4 REVISE / 9 APPROVE first-try** | All REVISE caught real defects, none were churn. |

- **Forge:** claude (this assistant) for every stage.
- **Gauge:** gemini (model `gemini-3.1-pro-preview` via `gemini` CLI 0.40.1) for every stage.
- **Skills invoked:** none (per `state.json.skillsUsed` for every stage). This is a pure-Python discovery-layer fix; no SystemVerilog or template-generation skill matched. Confirms CLAUDE.md's "Skill Routing Rules" — they did not apply here.

Branch contains 26 commits from forge/gauge/steel/stage-complete tags. Final code change: ~14 LOC in `src/piketype/discovery/scanner.py`, ~73 LOC new in `tests/test_scanner.py`.

---

## Memories to Save

### M-1 (feedback) — Preserve user-supplied minimal-change scope verbatim; surface gauge "improve it" suggestions as clarification questions

**Type:** `feedback`

**Name:** `feedback_minimal_change_preserve_scope.md`

**Content:**
> When the user invokes `/steel-specify` with an explicit, enumerated minimal patch (literal set entries, "minimal change" language, a verbatim code block), preserve that scope verbatim through Forge phases. Do not silently broaden the user-supplied list, swap to a "better" algorithm, or add reactive sub-features. Surface every Gauge "this could be expanded / optimized" suggestion as an Open Question (Q-N) for the clarification stage, and resolve in alignment with user intent unless the Constitution mandates otherwise.
>
> **Why:** In this workflow the Gauge (gemini) repeatedly raised:
> - Spec iter1: WARNING to extend `EXCLUDED_DIRS` from six to ~12 entries (`.mypy_cache`, `build`, `dist`, etc.).
> - Spec iter1: BLOCKING to mandate `pathlib.Path.walk()` pruning over the user's `rglob` post-filter ("anti-pattern", "severe I/O overhead").
>
> Both suggestions were technically defensible but contradicted the user's explicit `/steel-specify` prompt that named exactly six entries and labeled the rglob patch the "Real fix — Minimal change". The Forge correctly resisted: NFR-1 was rewritten to permit either strategy and clarification C-2 pinned `rglob` per user intent; FR-3 was tightened to "exactly six entries" via clarification C-1.
>
> **How to apply:** Whenever Gauge feedback proposes scope expansion or algorithmic substitution and the Constitution doesn't compel it, do NOT adopt it in the Forge revision. Instead, encode the trade-off as Q-N in the spec's Open Questions and let clarification surface it to the user. The user's explicit minimal-patch shape is the source of truth.

**Evidence:**
- `specs/015-scanner-exclude-venv-dirs/artifacts/specification/iter1-gauge.md` — quote: "BLOCKING — NFR-1 explicitly mandates that the exclusion check 'runs only for `.py` files already produced by `rglob`' ... implementer should use `pathlib.Path.walk()` to prune ..."
- `specs/015-scanner-exclude-venv-dirs/artifacts/specification/iter1-gauge.md` — quote: "WARNING — FR-3's list of excluded directories is too minimal ... It should explicitly include `.mypy_cache`, `.pytest_cache`, ..."
- `specs/015-scanner-exclude-venv-dirs/clarifications.md` C-1 + C-2 — Forge's resolution against the gauge in favor of user intent.

**Rationale:** This is non-obvious because the natural agent reflex is to incorporate review feedback. Without this discipline, /steel-specify drifts away from user-stated minimal-change requests through "helpful" Forge revisions. The pattern repeated again in clarification iter1 (predicate-ordering tweak in C-2 was an over-specification) — confirming this is a systemic tendency, not a one-off.

---

### M-2 (reference) — gemini-3.1-pro-preview gauge model is rate-limited; budget for retries

**Type:** `reference`

**Name:** `reference_gemini_gauge_rate_limits.md`

**Content:**
> The gauge configured in `.steel/config.json` (`gemini`) currently runs `gemini` CLI 0.40.1 against `gemini-3.1-pro-preview`. This model frequently returns HTTP 429 `RESOURCE_EXHAUSTED` ("No capacity available for model gemini-3.1-pro-preview"). The CLI retries internally with exponential backoff and typically succeeds within a few minutes, but a single gauge call can stall for 60–180s of wall-clock time.
>
> Plan workflow timing accordingly: each gauge call may take 1–3 minutes, not 5–15 seconds. For interactive `/steel-run-all` runs, expect total cycle times of 10–30 minutes for a small spec, dominated by gauge waits.

**Evidence:**
- `specs/015-scanner-exclude-venv-dirs/artifacts/task_breakdown/iter1-gauge-prompt.md` run produced a stderr trace beginning `Attempt 1 failed with status 429. Retrying with backoff... _GaxiosError: ... "code": 429, "message": "No capacity available for model gemini-3.1-pro-preview on the server" ...` — eventually succeeded after backoff.
- Subsequent gauge calls (task1 iter1 onward) succeeded immediately, showing the rate limit is intermittent.

**Rationale:** Workflow planning is harder without knowing the gauge call's wall-clock cost. Knowing that a 429 retry-storm on the gemini side is normal (not a workflow bug) prevents over-reaction (e.g., switching providers, killing the cli, retrying inside Steel-Kit).

---

### M-3 — none additional

I considered but rejected as memory candidates:
- "Existing fixtures contain `.git/HEAD` and `__pycache__/*.pyc`" — derivable from `find tests -type d -name '.git' -o -name '__pycache__'`. Not memory-worthy.
- "Use `.venv/bin/piketype` not `python -m piketype` for ad-hoc CLI runs" — already partially covered by the existing `project_venv_required_for_piketype.md` memory. Possibly worth a one-line addendum: console-script invocation is also valid.
- "Project memory: scanner.py:11 EXCLUDED_DIRS frozenset" — derivable from `git grep EXCLUDED_DIRS`. Not memory-worthy.

---

## Skill Updates

### S-1 — `/steel-specify`: handle re-entry from a previously completed workflow

**Skill:** `/steel-specify` (file: `~/.claude/skills/steel-specify` or equivalent in the Steel-Kit plugin layout — wherever the `/steel-specify` slash command's instructions live).

**Issue found:** When the user invokes `/steel-specify` after a prior workflow has fully completed, `state.json.currentStage` is `retrospect` (or whatever the last stage was) with `retrospect.status: "complete"`. The skill's prerequisite check requires `currentStage == "specification"`, which fails. The user must either run `/steel-clean` (which removes prior artifacts) or manually reset state. In this run the user explicitly said "no. do not clear. just `reset and proceed` the `/steel-specify`", and the assistant had to inline-reset state.json by hand.

Quote from the early turn: "The `/steel-specify` prerequisites are not met. Two options: 1. Run `/steel-clean` ... 2. Manually reset `.steel/state.json` to a fresh `specification` stage and proceed."

**Proposed change:** Add a new step between the prerequisite check and step 1:

> 0a. If `.steel/state.json` exists and shows a previously-completed workflow (all stages complete OR `currentStage == "retrospect"` with `retrospect.status == "complete"`), and `--id` was not provided pointing at a different in-progress spec, ask the user:
>
>    > "A previous workflow (`<previous specId>`) is fully complete. Start a new workflow with this prompt? [y / clean / cancel]"
>
> - **y**: reset `state.json` to fresh `specification:pending` (preserving past tags and artifacts), then proceed to step 1.
> - **clean**: invoke `/steel-clean` first, then proceed.
> - **cancel**: stop.

**Expected impact:** Removes one round-trip clarification at workflow boundaries (the user's "no. do not clear. just reset and proceed" turn would not have been needed). Saves ~30s of friction per workflow start when reusing a project that has prior completed specs.

---

### S-2 — `/steel-clean`: clarify scope (does NOT remove top-level spec.md/plan.md/etc.)

**Skill:** `/steel-clean`

**Issue found:** When the user reflexively typed `/steel-clean` (intending to wipe and start over), the skill's "Show what will be removed" step listed:
> - `specs/<specId>/artifacts/` (iteration artifacts only, not spec/plan/retrospect files)

This is correct, but the user's reaction was "no. do not clear" — suggesting the user wasn't sure whether the spec/plan/retrospect files would survive. The skill's confirmation prompt is currently:
> "This will remove iteration artifacts for spec `<specId>` and reset workflow state. Continue?"

**Proposed change:** Make the confirmation prompt explicit about what is preserved:

> "This will remove iteration artifacts for spec `<specId>` (forge/gauge iteration files under artifacts/) and reset workflow state.json. The top-level spec.md, plan.md, tasks.md, validation.md, retrospect.md, clarifications.md will be PRESERVED. Continue?"

**Expected impact:** Reduces user uncertainty about whether prior approved deliverables (spec.md etc.) will be lost. Would have avoided the user's "no, do not clear" interrupt in this run.

---

### S-3 — `/steel-implement`: the "verification task" subclass deserves a lighter Gauge prompt template

**Skill:** `/steel-implement`

**Issue found:** Tasks T3, T4, T5 are pure verification (run a tool, capture output, no code change). The full Gauge prompt template (~150 lines, mandating "full git diff, full file content, security review, OWASP top 10") is overkill for "did `0 errors` come back from basedpyright?". In this run I shortened the Gauge prompt for T3/T4/T5 organically, and gemini's responses for those were correspondingly terse ("None. VERDICT: APPROVE").

**Proposed change:** Add to `/steel-implement` step 3e a new template hint:

> If the task is a pure verification step (no source files modified — i.e., the artifact `task<N>-iterM-forge.md` lists `Files Changed: None`), use a streamlined Gauge prompt that asks:
> 1. Did the Forge run the right command?
> 2. Did the reported result match the verification criteria in `tasks.md`?
> 3. Was cleanup performed?
>
> Skip the "full git diff", "full file content", "security review", "OWASP top 10" sections — they are not applicable to verification-only tasks.

**Expected impact:** Saves ~80 lines of prompt template per verification task and reduces gauge token cost. Faster gauge turns. No loss of rigor for these tasks because there's nothing else for the gauge to check.

---

### S-4 — Steel-Kit overall: small bug-fix specs incur high ceremony cost

**Skill:** All Steel-Kit stage commands.

**Issue found:** This bug fix produced 26 commits, 13 forge-gauge cycles, ~30 min of wall-clock time, and ~30 artifact files for what is fundamentally a 14-LOC code change in one file. While each iteration caught real defects (no churn), the ratio of process-output to code-output is high.

**Proposed change:** This is a balance point, not a clear defect. Two options worth considering, but neither is being proposed as a change to apply now (this is a NOTE not a BLOCKING):
- (a) A `--fast` mode for `/steel-run-all` that skips clarification when the spec emerges from `/steel-specify` with zero `[NEEDS CLARIFICATION]` markers AND merges planning+task_breakdown into one step for single-file changes.
- (b) A `/steel-bugfix "<one-line-description>"` shortcut that takes spec→plan→implementation→validation in one pass with reduced ceremony, suitable for small fixes.

**Expected impact (if applied):** Would reduce 26 commits → ~6-8 for similar one-file fixes. Skipping clarification would cost the value of catching the FR-3 / NFR-1 / AC-4 over-specifications observed here, so this is NOT a free lunch — surface as user-opt-in only.

**Decision:** Surface as a user discussion point, not a recommended change. Steel-Kit's value proposition is rigor; that rigor genuinely caught defects in this run.

---

## Process Improvements

### P-1 — Bottlenecks: Forge over-specification of NFRs and ACs

**Issue:** Both REVISE verdicts (spec iter1, clarification iter1) were caused by the Forge writing requirements that prescribed implementation details rather than observable behavior:
- Spec NFR-1 v1: "runs only for `.py` files already produced by `rglob`" — over-specified the post-filter strategy as a hard requirement.
- Spec AC-4 v1: ambiguous wording that contradicted itself on whether `.git/piketype/foo.py` should be returned.
- Clarification C-1 v1: claimed "exactly these six entries, in this order" — semantically nonsense for a frozenset.
- Clarification C-2 v1: predicate-ordering "tweak" — over-specified an impl detail.

**Evidence:**
- `artifacts/specification/iter1-gauge.md` — 2 BLOCKING (NFR-1, AC-4).
- `artifacts/clarification/iter1-gauge.md` — 2 BLOCKING (C-1, C-2 mismatches), 1 WARNING (missing OOS-7).

**Classification:** Each REVISE was **(a) caught a real defect**. Zero churn.

**Proposed fix:** Add a Forge-side check during specification: "Before committing the spec, verify that no FR or NFR mandates a specific function call, library, or syntactic shape unless the user explicitly required it. NFRs should describe properties (perf, determinism, type-safety), not implementations." This would have pre-empted the NFR-1 over-specification.

---

### P-2 — Forge-Gauge dynamics: Gauge (gemini) consistently raised optimization suggestions as BLOCKING

**Issue:** Multiple BLOCKING items were optimization-flavored, not constitution-violations:
- Spec iter1 BLOCKING: "use Path.walk() instead of rglob".
- (Several similar non-blocking suggestions across stages.)

The Gauge had no built-in awareness that scope decisions belong to the user, not the gauge. The Forge correctly resisted, but each resistance cost an iteration.

**Evidence:** `artifacts/specification/iter1-gauge.md` line "BLOCKING — NFR-1 explicitly mandates that the exclusion check 'runs only for `.py` files already produced by `rglob`' ... is an anti-pattern".

**Classification of all REVISE verdicts:**
- Spec iter1: (a) caught real defect (AC-4 contradiction was real); over-classified NFR-1 BLOCKING that should have been WARNING.
- Clarification iter1: (a) caught real defect (semantic mismatches were real).

So strictly the gauge was doing its job. The fix is in the gauge prompt, not the gauge model: my gauge prompts already include "the Constitution is the highest authority" and "do NOT raise optimization suggestions as BLOCKING" hints in iter2+ rounds. Iter1 prompts could include those hints from the start.

**Proposed fix:** Update the default gauge prompt template (in each `/steel-*` skill) to include from iter1:

> The Project Constitution is the highest authority over the gauge's preferences. Do NOT classify any review item as BLOCKING unless it (a) violates a Constitution principle/standard/constraint, (b) introduces a logical contradiction, or (c) leaves a spec/plan internally inconsistent. Optimization suggestions ("use X instead of Y") are at most WARNING unless the Constitution mandates the alternative.

**Expected impact:** Iter1 false-BLOCKING rate drops; Forge spends fewer cycles relitigating optimizations.

---

### P-3 — Constitution gaps

None observed. The Constitution covered every guidance question that arose in this workflow:
- Frozen dataclasses / Python conventions: relevant to scanner.py's idioms.
- `unittest.TestCase` testing: covered AC-6 directly.
- basedpyright strict: covered AC-7 / NFR-3 directly.
- Conventional Commits: covered branch + commit hygiene.
- Branching from develop with `feature/<name>`: handled at /steel-specify branch creation.

No constitution amendments proposed.

---

### P-4 — Workflow gaps

**Minor:** Workflow re-entry after a previous-workflow-complete state required manual reset (covered above as S-1).

**Minor:** `.steel/.gitignore` excludes `.steel/tasks.json`, but Steel-Kit's `/steel-tasks` step writes it, then `/steel-implement` reads it. This is fine, but the first time I tried to commit it during /steel-tasks, the gitignore correctly blocked it. The skill instruction ("Also save a JSON version to .steel/tasks.json") doesn't note that this file is intentionally ungitignored — a future maintainer might be surprised.

**Proposed fix:** Add to `/steel-tasks` step 4 a parenthetical: "(Note: `.steel/tasks.json` is gitignored by default in Steel-Kit projects; do not attempt to commit it.)"

**Expected impact:** Saves a confused 5-second moment for the next AI/human running this workflow.

---

## Summary

- **13 forge-gauge cycles, 4 REVISE verdicts, 0 churn.** Every REVISE caught a real defect.
- **Two memories worth saving** (M-1 minimal-change scope discipline, M-2 gemini rate-limit awareness).
- **Three skill updates worth applying** (S-1 workflow re-entry, S-2 /steel-clean confirmation, S-3 lighter gauge prompt for verification tasks). S-4 (small-spec ceremony cost) is informational.
- **Two process improvements** (P-1 Forge over-specification check, P-2 default gauge prompt clarification).
- **No constitution amendments needed.**
