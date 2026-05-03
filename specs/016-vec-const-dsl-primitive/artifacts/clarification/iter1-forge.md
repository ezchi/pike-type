# Clarifications: 016-vec-const-dsl-primitive

**Iteration:** 1
**Source:** User answers + Constitution + Forge analysis

## Resolutions

### C-1. Q-1 — Signed values: REJECT [SPEC UPDATE]

**Open question:** Should `VecConst` accept signed values (two's-complement representation), or strict-reject negative resolved values?

**Resolution:** Strict reject. No `signed=` keyword is added in v1. Negative resolved values raise `ValidationError` per FR-7 (overflow check) and FR-8 (negative-rejection). No two's-complement support.

**Why:** User answer "reject signed value" + the original `/steel-specify` prompt showed only unsigned positive values (`16'h8100`, `8'd6`, `8'd17`). Adding a `signed=` flag now would speculatively widen the API surface for use cases the user has not asked for; per memory `feedback_minimal_change_preserve_scope.md`, defer until a real signed use case lands.

**How to apply:** Future signed support, if ever needed, is a separate spec that can add a `signed=False` keyword arg and an `'sh` / `'sd` / `'sb` SV literal mode. Until then, FR-8 stands.

**Spec impact:** Remove the trailing parenthetical "(See Open Q-1 for whether to allow signed two's-complement representation.)" from FR-8 and "(See Open Q-1.)" from OOS-1. Q-1 removed from Open Questions.

---

### C-2. Q-2 — Naming convention: VERBATIM [NO SPEC CHANGE]

**Open question:** Should the generator enforce a naming convention (e.g., `UPPER_SNAKE_CASE`, `LP_` prefix) on the Python variable name, and reject lowercase names at validation time?

**Resolution:** No enforcement. Emit the Python variable name verbatim into SV (current FR-12). Mixed-case, leading-underscore, no-prefix — all accepted. This matches existing `Const()` behavior.

**Why:** User answer "verbatim". Consistent with how `Const()` works today. The Constitution §Coding Standards Python rule for `UPPER_SNAKE_CASE` applies to the Python source side (which is the user's code, validated separately by linters); the generator does not police it on emission.

**How to apply:** None. FR-12 stays.

**Spec impact:** Remove the trailing parenthetical "(See Open Q-2 for whether to mandate `LP_` prefix or uppercase.)" from FR-12. Q-2 removed from Open Questions.

---

### C-3. Q-3 — Manifest schema: SEPARATE `vec_constants` array (Option A) [SPEC UPDATE]

**Open question:** Manifest layout — separate `vec_constants:` array, or fold into `constants:` array with a `kind` discriminator?

**Resolution:** Option A. The manifest gets a new top-level array `vec_constants` per module, sibling to the existing `constants` array. The existing `constants` schema is BYTE-IDENTICAL — no `"kind"` field is added to legacy entries.

Concrete shape (per module):
```json
"constants": [
  { "name": "FOO", "resolved_signed": true, "resolved_value": 3, "resolved_width": 32, "source": {...} }
],
"vec_constants": [
  { "name": "LP_ETHERTYPE_VLAN", "value": 33024, "width": 16, "base": "hex", "source": {...} }
]
```

**Why:** User answer "Option A". Constitution Principle 3 ("Deterministic output. Generated code must be byte-for-byte reproducible given the same inputs.") makes adding a `"kind"` field to every existing `constants` entry expensive — it would invalidate every existing golden manifest under `tests/goldens/gen/*/piketype_manifest.json`. The two-array shape is a pure addition; no existing golden manifest needs to change.

**How to apply:** None for legacy `constants:` consumers. New `vec_constants:` consumers iterate the new array.

**Spec impact:** Remove the trailing parenthetical "(See Open Q-3 for whether to fold into `constants` instead.)" from FR-18. Q-3 removed from Open Questions.

---

### C-4. Q-4 — Width upper bound: KEEP AT 64 [SPEC UPDATE]

**Open question:** Width upper bound 64, or lift for IPv6 / hash use cases?

**Resolution:** Keep at 64. Matches existing scalar 64-bit signed cap and existing `Const()` 32/64 ceiling. IPv6 (128-bit) and hash-constant use cases are real but speculative; defer until a concrete user lands.

**Why:** User answer "keep upper bound at 64". Project-wide alignment trumps speculative extensibility. Per memory `feedback_minimal_change_preserve_scope.md`, narrow scope is preferred when no concrete user use case is on file.

**How to apply:** None. FR-5 stays.

**Spec impact:** Remove the trailing parenthetical "(See Open Q-3 for whether to lift this.)" from FR-5 (note: stale Q-3 reference — should have been Q-4 after iter2 renumbering). Same for "(See Open Q-3.)" in OOS-2 (also stale). Q-4 removed from Open Questions.

---

## Summary

- **3 [SPEC UPDATE] clarifications** (C-1, C-3, C-4) — all editing parenthetical Q-references only; no FR semantics change.
- **1 [NO SPEC CHANGE] clarification** (C-2) — already aligned.
- **All 4 Open Questions resolved** and removed from spec.md.
- **No FR/NFR/AC semantics changed** by this clarification round; the resolutions all confirm existing defaults.
