# Performance Measurements — Jinja Template Migration

Each row records one `python tools/perf_bench.py --fixture struct_padded
--iterations 5` invocation (one warm-up + 5 measured iterations,
median/min/max in milliseconds).

The `baseline` row was captured before any backend migration commit,
on `feature/010-jinja-template-migration` after Phase 0 commits T-01..T-05.
At capture time the emitters were still the legacy inline string
builders, so this number reflects pre-migration timing per CL-4.

| stage          | backend | median_ms | min_ms | max_ms |
|----------------|---------|-----------|--------|--------|
| baseline       | -       | 2.448     | 2.261  | 2.812  |
| py-complete    | py      | 12.016    | 11.824 | 12.170 |
| cpp-complete   | cpp     | 12.885    | 12.833 | 13.312 |
| sv-complete    | sv      | 14.862    | 13.573 | 15.143 |
| feature-final  | all     | 13.861    | 13.708 | 14.153 |

Subsequent rows are appended at:

- `py-complete` after T-13 (Phase 1 cleanup commit lands).
- `cpp-complete` after T-20.
- `sv-complete` after T-27.
- `feature-final` during the validation stage (T-29) for AC-F4.

AC-F4 requires `feature-final.median_ms <= 1.25 * baseline.median_ms`
(NFR-1).

**Status note (after py-complete):** the Python migration alone
exceeds the 1.25× budget. Profile shows ~16 ms is template
compilation (parse + compile to Python bytecode), which happens
once per `emit_py` call because FR-2 mandates the env be
constructed per-call (not module-global). For a single-module
fixture this overhead is dominant relative to the legacy ~2.4 ms
inline string-build time. Mitigations to evaluate before
feature-final:

- `jinja2.FileSystemBytecodeCache` (writes to a cache dir;
  off-spec for "no new runtime dependency" but uses stdlib
  pickle).
- Pre-compile templates as Python modules at backend import time
  (does not violate FR-2 because the env is still per-call; the
  loader uses a precompiled module cache).
- Renegotiate NFR-1 budget if neither mitigation holds.

Decision deferred to validation stage. C++ and SV migrations
proceed in their respective phases.

**AC-F4 verdict at feature-final:** `feature-final.median_ms = 13.861`,
`baseline.median_ms = 2.448`. Ratio = 5.66×, well outside the
1.25× budget. The NFR-1 budget was naively optimistic for a
migration where each `gen` call recompiles three Jinja
environments (FR-2 mandate). **AC-F4 is NOT met.** Documented
as a known issue for retrospect / future amendment. Mitigations
to evaluate before any spec amendment:

- **Bytecode caching** via `jinja2.Environment(bytecode_cache=...)`
  using `MemcachedBytecodeCache` (in-memory, per-process) or
  `FileSystemBytecodeCache`. Would amortize compile cost across
  multiple `gen` invocations in CI loops but doesn't help a single
  `gen` call.
- **Module-level env caching** (would require amending FR-2's
  "constructed once per emit_<lang> call" rule). Module-level
  caching brings repeat-call cost down to render-only (~5 ms),
  still a ~2× regression but within 25% if amended to 100%.
- **Spec amendment**: relax NFR-1 to 250% or 600% given
  measurement realities. The migration's correctness gates
  (byte-parity goldens, lint, view-model tests) are all met;
  only the perf gate fails.

Capture environment:

- Host: Darwin 25.4.0 (arm64), Apple Silicon
- Python: 3.13 (project venv at `.venv/`)
- Jinja2: per `uv.lock` (>=3.1)
