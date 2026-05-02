"""Reserved-keyword sets for the three target languages.

This module owns frozen sets of reserved keywords for the languages that
``piketype`` emits code into, plus a single classifier helper used by the
validation engine. The sets are literal snapshots — they are not computed at
import time — so error output is byte-identical across runs (Constitution
principle 3, Determinism).

Standard references and authoring decisions
-------------------------------------------

SystemVerilog (``SV_KEYWORDS``)
    Union of the reserved keywords listed in IEEE Std 1800-2017 Annex B
    ("Keywords") and any reserved-word additions in IEEE Std 1800-2023.
    Cross-checked against the IEEE 1800-2017 standard text and the SV
    keyword tables maintained by Verilator's lexer
    (``include/verilated_funcs.h`` keyword table). The 1800-2023 standard
    is a maintenance revision over 1800-2017; no keywords were added in
    1800-2023 over 1800-2017 according to both reference sources used at
    capture time. If a future audit identifies a 1800-2023 addition not
    present here, append it and bump the comment block.

C++ (``CPP_KEYWORDS``)
    Reserved keywords from ISO/IEC 14882:2020 (C++20, draft N4861, §2.13),
    *including* the coroutine keywords ``co_await``, ``co_yield``,
    ``co_return`` (which are language-level reserved keywords, not
    contextual identifiers); plus the alternative tokens (``and``, ``or``,
    ``not``, ``xor``, ``bitand``, ``bitor``, ``compl``, ``and_eq``,
    ``or_eq``, ``xor_eq``, ``not_eq``); plus the contextual identifiers
    ``import`` and ``module`` (these participate in module-declaration
    parsing and present a forward-compat collision risk for module
    filenames). Excludes ``final`` and ``override`` — these are legal as
    identifiers in any non-declarator position and rejecting them would
    over-restrict per Constitution principle 4.

Python (``PY_HARD_KEYWORDS`` / ``PY_SOFT_KEYWORDS``)
    Snapshot of ``keyword.kwlist`` and ``keyword.softkwlist`` for CPython
    3.12.x. The hard keyword list (35 entries) has been stable across
    CPython 3.10–3.14; the soft keyword list (4 entries: ``_``, ``case``,
    ``match``, ``type``) reached its current shape in CPython 3.12 with
    the addition of ``type`` for PEP 695 type-statement syntax. The
    ``tests/test_keyword_set_snapshot.py`` unit test asserts these
    snapshots equal the live ``keyword`` module under a CPython 3.12.x
    interpreter and skips on other minor versions. Snapshot captured
    against the literal kwlist content for CPython 3.12.x as published
    in the cpython source tree.

The ``keyword`` stdlib module is intentionally NOT imported at runtime in
this module — see NFR-4 (no external dependencies / no late-binding). The
test file uses ``keyword`` only inside the snapshot canary.
"""

from __future__ import annotations


# IEEE 1800-2017 reserved keywords (Annex B). Sorted alphabetically.
# 1800-2023 adds no new reserved keywords over 1800-2017 (per cross-check
# against the Verilator lexer keyword table at capture time).
SV_KEYWORDS: frozenset[str] = frozenset({
    "accept_on", "alias", "always", "always_comb", "always_ff", "always_latch",
    "and", "assert", "assign", "assume", "automatic", "before", "begin", "bind",
    "bins", "binsof", "bit", "break", "buf", "bufif0", "bufif1", "byte", "case",
    "casex", "casez", "cell", "chandle", "checker", "class", "clocking", "cmos",
    "config", "const", "constraint", "context", "continue", "cover", "covergroup",
    "coverpoint", "cross", "deassign", "default", "defparam", "design", "disable",
    "dist", "do", "edge", "else", "end", "endcase", "endchecker", "endclass",
    "endclocking", "endconfig", "endfunction", "endgenerate", "endgroup",
    "endinterface", "endmodule", "endpackage", "endprimitive", "endprogram",
    "endproperty", "endsequence", "endspecify", "endtable", "endtask", "enum",
    "event", "eventually", "expect", "export", "extends", "extern", "final",
    "first_match", "for", "force", "foreach", "forever", "fork", "forkjoin",
    "function", "generate", "genvar", "global", "highz0", "highz1", "if", "iff",
    "ifnone", "ignore_bins", "illegal_bins", "implements", "implies", "import",
    "incdir", "include", "initial", "inout", "input", "inside", "instance", "int",
    "integer", "interconnect", "interface", "intersect", "join", "join_any",
    "join_none", "large", "let", "liblist", "library", "local", "localparam",
    "logic", "longint", "macromodule", "matches", "medium", "modport", "module",
    "nand", "negedge", "nettype", "new", "nexttime", "nmos", "nor",
    "noshowcancelled", "not", "notif0", "notif1", "null", "or", "output",
    "package", "packed", "parameter", "pmos", "posedge", "primitive", "priority",
    "program", "property", "protected", "pull0", "pull1", "pulldown", "pullup",
    "pulsestyle_ondetect", "pulsestyle_onevent", "pure", "rand", "randc",
    "randcase", "randsequence", "rcmos", "real", "realtime", "ref", "reg",
    "reject_on", "release", "repeat", "restrict", "return", "rnmos", "rpmos",
    "rtran", "rtranif0", "rtranif1", "s_always", "s_eventually", "s_nexttime",
    "s_until", "s_until_with", "scalared", "sequence", "shortint", "shortreal",
    "showcancelled", "signed", "small", "soft", "solve", "specify", "specparam",
    "static", "string", "strong", "strong0", "strong1", "struct", "super",
    "supply0", "supply1", "sync_accept_on", "sync_reject_on", "table", "tagged",
    "task", "this", "throughout", "time", "timeprecision", "timeunit", "tran",
    "tranif0", "tranif1", "tri", "tri0", "tri1", "triand", "trior", "trireg",
    "type", "typedef", "union", "unique", "unique0", "unsigned", "until",
    "until_with", "untyped", "use", "uwire", "var", "vectored", "virtual", "void",
    "wait", "wait_order", "wand", "weak", "weak0", "weak1", "while", "wildcard",
    "wire", "with", "within", "wor", "xnor", "xor",
})


# C++20 reserved keywords (N4861 §2.13). Includes coroutine keywords and
# alternative tokens. Excludes contextual identifiers `final` and `override`.
# Includes contextual identifiers `import` and `module` (forward-compat risk).
CPP_KEYWORDS: frozenset[str] = frozenset({
    # Reserved keywords.
    "alignas", "alignof", "asm", "auto", "bool", "break", "case", "catch",
    "char", "char8_t", "char16_t", "char32_t", "class", "co_await",
    "co_return", "co_yield", "concept", "const", "consteval", "constexpr",
    "constinit", "const_cast", "continue", "decltype", "default", "delete",
    "do", "double", "dynamic_cast", "else", "enum", "explicit", "export",
    "extern", "false", "float", "for", "friend", "goto", "if", "inline",
    "int", "long", "mutable", "namespace", "new", "noexcept", "nullptr",
    "operator", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return", "short", "signed", "sizeof",
    "static", "static_assert", "static_cast", "struct", "switch", "template",
    "this", "thread_local", "throw", "true", "try", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "virtual", "void", "volatile",
    "wchar_t", "while",
    # Alternative tokens (lex.digraph).
    "and", "and_eq", "bitand", "bitor", "compl", "not", "not_eq", "or",
    "or_eq", "xor", "xor_eq",
    # Contextual identifiers retained for forward-compat (modules).
    "import", "module",
})


# CPython 3.12.x ``keyword.kwlist`` snapshot.
PY_HARD_KEYWORDS: frozenset[str] = frozenset({
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
})


# CPython 3.12.x ``keyword.softkwlist`` snapshot.
PY_SOFT_KEYWORDS: frozenset[str] = frozenset({
    "_", "case", "match", "type",
})


def keyword_languages(identifier: str) -> tuple[str, ...]:
    """Return alphabetically-sorted target-language labels in which ``identifier``
    is a reserved keyword.

    Returned labels are drawn from ``{"C++", "Python", "Python (soft)",
    "SystemVerilog"}``. Empty tuple means the identifier is free of keyword
    collisions in all three target languages.

    Hard Python wins over soft Python: if an identifier is in both
    ``PY_HARD_KEYWORDS`` and ``PY_SOFT_KEYWORDS`` (impossible in CPython 3.12
    where the two sets are disjoint, but defensive against a future drift),
    only the hard label is emitted. The sort key is the label string itself,
    so ``"Python"`` sorts before ``"Python (soft)"``.
    """
    hits: list[str] = []
    if identifier in CPP_KEYWORDS:
        hits.append("C++")
    if identifier in PY_HARD_KEYWORDS:
        hits.append("Python")
    elif identifier in PY_SOFT_KEYWORDS:
        hits.append("Python (soft)")
    if identifier in SV_KEYWORDS:
        hits.append("SystemVerilog")
    hits.sort()
    return tuple(hits)
