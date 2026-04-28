# Gauge Review — Iteration 1

### ISSUE-1: Power-of-two rule contradicts valid `multiple_of(24)`
**Severity:** BLOCKING
**Section:** User Stories / FR-2 / AC-2
**Description:** US-3 lists "non-power-of-two" as invalid, but FR-2 explicitly says power-of-two is not required and AC-2 requires `multiple_of(24)` to be valid. Fix the spec by removing "non-power-of-two" from invalid examples or making power-of-two mandatory everywhere.

### ISSUE-2: SV `pack` width semantics are wrong or undefined
**Severity:** BLOCKING
**Section:** FR-3 / FR-4 / AC-1
**Description:** Existing SV `LP_*_WIDTH` and `pack_*` operate on compact data width, while byte serialization uses per-field byte padding. For `Bit(5) + Bit(12)`, data width is 17 bits and natural serialized width is 24 bits. FR-4 says append 8 alignment bits to `pack`, which produces 25 bits, not AC-1's 32-bit serialized width. The spec must decide whether `pack` remains data-only or becomes serialized-width including per-field padding and trailing alignment, then define `LP_*_WIDTH`, offsets, and concat order accordingly.

### ISSUE-3: C++ and Python `pack/unpack` acceptance is impossible as written
**Severity:** BLOCKING
**Section:** AC-8
**Description:** The current C++ and Python generated APIs expose `to_bytes/from_bytes`, not struct-level `pack/unpack`. AC-8 requires pack/unpack round-trips in SV, C++, and Python without defining those APIs. Either restrict AC-8 to SV or explicitly add C++/Python packed-bit APIs to FR-5 and FR-6.

### ISSUE-4: Template-first requirement is not specified
**Severity:** BLOCKING
**Section:** Functional Requirements / Project Constitution alignment
**Description:** The constitution says generated output changes must be template-first where practical. The spec only names emitter behavior and gives no template/view-model requirements. Add explicit backend template updates, view-model fields, and expected generated output changes, or state why this feature is exempt.

### ISSUE-5: Negative validation tests are underspecified
**Severity:** WARNING
**Section:** Acceptance Criteria / Tests
**Description:** AC-3 through AC-5 require validation failures, but the test plan only explicitly calls for positive golden-file tests. Add negative unittest/CLI fixture coverage for invalid N, duplicate multiple_of, and add_member after multiple_of, with expected error substrings.

### ISSUE-6: Runtime integer validation leaves `bool` ambiguous
**Severity:** WARNING
**Section:** FR-2
**Description:** `bool` is an `int` subclass in Python. "N is a positive integer" does not say whether `multiple_of(True)` is rejected. Specify `type(N) is int` and reject `bool`, or explicitly allow it.

VERDICT: REVISE
