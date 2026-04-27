# Gauge Review — Iteration 2

## Issues

### [BLOCKING] Reserved C++ Namespace Validation Is Still Incomplete
- **Requirement:** FR-2 / AC-7
- **Issue:** FR-2 still permits reserved C++ identifiers. C++ reserves identifiers containing `__` anywhere, not only with a `__` prefix. It also reserves names beginning with `_` in the global namespace, so `--namespace _foo` is unsafe. The spec also allows `--namespace std::x`, which generates declarations inside `std`, which is not valid user code.
- **Suggestion:** Update FR-2 and AC-11 to reject any segment containing `__`, reject the first segment if it starts with `_`, and reject `std` as the first segment. Add negative CLI tests for these cases.

### [WARNING] Runtime C++ Header Scope Is Ambiguous
- **Requirement:** FR-5 / FR-7 / AC-1
- **Issue:** FR-7 says "All emitted C++ headers in the run use the same namespace prefix," but the project also emits `cpp/runtime/typist_runtime.hpp`. AC-1 narrows this to module namespaces, so the runtime header behavior is unclear.
- **Suggestion:** State explicitly that `--namespace` affects generated module C++ headers only, and that runtime C++ headers keep their existing namespace and include guard. If runtime should change too, add explicit requirements and acceptance criteria.

### [WARNING] Positive Multi-Module Coverage Is Not Explicit
- **Requirement:** FR-7 / AC-10
- **Issue:** FR-7 requires the override to apply to every discovered module, but AC-10 does not explicitly require the golden fixture to contain multiple discovered modules. A single-module positive golden could pass while missing the main FR-7 behavior.
- **Suggestion:** Require the positive golden-file case to include at least two discovered modules with different path-derived namespaces, and assert both C++ headers use the same override prefix.

## VERDICT: REVISE
