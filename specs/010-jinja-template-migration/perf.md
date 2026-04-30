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

Subsequent rows are appended at:

- `py-complete` after T-13 (Phase 1 cleanup commit lands).
- `cpp-complete` after T-20.
- `sv-complete` after T-27.
- `feature-final` during the validation stage (T-29) for AC-F4.

AC-F4 requires `feature-final.median_ms <= 1.25 * baseline.median_ms`
(NFR-1).

Capture environment:

- Host: Darwin 25.4.0 (arm64), Apple Silicon
- Python: 3.13 (project venv at `.venv/`)
- Jinja2: per `uv.lock` (>=3.1)
