# Gauge Review -- Iteration 1

## Issues

### [BLOCKING] Scope Contradicts The Acceptance Criteria
- **Requirement:** Overview / FR-3 / AC-1 / AC-6
- **Issue:** The overview says every generated C++ `constexpr` must use `UPPER_SNAKE_CASE`, and the out-of-scope list only excludes variables that are not `constexpr`. That is not what the requirements or acceptance criteria enforce. The C++ emitter also generates local `constexpr std::uint64_t mask` variables in inline scalar encode/decode helpers (`src/typist/backends/cpp/emitter.py:599`, `:637`, `:648`), and the current goldens contain those lowercase `constexpr` names (`tests/goldens/gen/struct_signed/cpp/alpha/typist/types_types.hpp:200`, `:217`). FR-3 only covers `kMinValue` and `kMaxValue` inside `validate_<field>`, and AC-6 only rejects `kCamelCase` constexpr names. An implementation can leave `mask` lowercase, pass AC-1 and AC-6 as written, and still violate the overview.
- **Suggestion:** Pick one scope. If the feature is only a `kCamelCase` rename, narrow the overview, user story, and out-of-scope wording to say that. If the feature is truly "all generated C++ constexpr identifiers are `UPPER_SNAKE_CASE`," add `mask -> MASK` coverage for encode/decode helper locals and make AC-6 check all generated non-user-defined `constexpr` identifiers, not only `kCamelCase`.

### [BLOCKING] Reference Update Requirements Are Not Exhaustive
- **Requirement:** FR-1 / FR-2 / AC-1
- **Issue:** FR-1 says references must be updated in method bodies such as `to_bytes`, `from_bytes`, and `validate_value`, but scalar alias generation also uses `kByteCount` in the wide-scalar default constructor initializer (`src/typist/backends/cpp/emitter.py:303`) and in `validate_value` (`:322`). The named method list is too narrow. If an implementer follows the text literally, generated C++ can still reference removed `k...` symbols after declarations are renamed.
- **Suggestion:** Require all references in each generated class scope to be updated, including constructor initializer lists, constructors, all public member functions, private helpers, and helper-local expressions. Do not limit the requirement to a parenthetical method list.

### [WARNING] Constitution Alignment Is Overstated
- **Requirement:** Overview / US-1 / Constitution alignment
- **Issue:** The spec says the project constitution mandates `UPPER_SNAKE_CASE` for constants, but the actual constitution places that rule under Python naming conventions for module-level constants (`.steel/constitution.md:35-39`). The generated-code constitution section covers machine-readable headers, template preference, include guards, and package layout; it does not define C++ `constexpr` naming. The feature can still be a valid style decision, but the stated constitutional basis is wrong.
- **Suggestion:** Rephrase the rationale as a project style decision for generated C++ output, or amend/cite an explicit generated C++ naming rule in the constitution.

### [WARNING] Template-First Exemption Is Not Justified
- **Requirement:** Out of Scope / Constitution alignment
- **Issue:** The spec puts Jinja2 template work out of scope. The constitution says new or changed generated outputs should be backed by templates wherever practical (`.steel/constitution.md:47-51`). This rename may be small enough to exempt, but the spec does not say why direct emitter string edits are acceptable here.
- **Suggestion:** Add a short explicit exemption: this feature is a mechanical rename in existing string-built emitters and does not introduce new generated structure, so template migration is deferred.

VERDICT: REVISE
