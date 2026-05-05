# Spec Diff — Clarification Iteration 2 (delta on iter1)

## Out of Scope — OOS-7 added

**Before:** OOS-6 was the last entry; no symlink language anywhere in the spec body.

**After:** New entry appended:
> **OOS-7.** Resolving symlinks before the excluded-directory check. A symlink in `repo_root` that points to a path physically under an excluded directory name (e.g., `repo_root/extlib -> /opt/projectx/.venv/...`) will NOT be excluded by this fix; only directly named `.venv/`, `__pycache__/`, etc. inside `repo_root` are filtered. See clarification C-3.

**Source clarification:** C-3 (now [SPEC UPDATE], promoted from [NO SPEC CHANGE]).

---

## Changelog — entry added

**Before:** Four entries from iter1.

**After:** Same four iter1 entries plus:
> - [Clarification iter2] OOS-7: added; symlinks pointing into excluded paths are NOT resolved by this fix (C-3, promoted from [NO SPEC CHANGE] to [SPEC UPDATE] per Gauge iter1 WARNING).

---

## Header

`Status:` updated from `Clarified (post-Clarification iteration 1)` → `Clarified (post-Clarification iteration 2)`.

---

## clarifications.md — also updated

- C-1 spec-impact line: dropped the "in this order" phrase (frozenset is unordered; the phrase was inaccurate per Gauge iter1 BLOCKING #1). Spec FR-3 unchanged.
- C-2 resolution: dropped the predicate-ordering "tweak" sentence. NFR-1 in spec.md is unchanged because the tweak was an over-specification of an implementation detail (Python's `and` short-circuits). Spec NFR-1 unchanged.
- C-3 marker flipped from [NO SPEC CHANGE] to [SPEC UPDATE]; spec impact now lists OOS-7.
- Summary recount: 4 [SPEC UPDATE] (was 3), 1 [NO SPEC CHANGE] (was 2).

---

## Sections NOT Modified

- All FRs (FR-1 through FR-8)
- All NFRs (NFR-1 through NFR-4)
- All ACs (AC-1 through AC-7)
- OOS-1 through OOS-6
- Risks, References, Overview, Background, User Stories
