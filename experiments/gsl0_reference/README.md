# GSL-0 candidate reference experiment

**NOT the production compiler**. Isolated prototype for testing proposed grammar,
refs, types, provenance and deterministic candidate IR. Its output is never ratified
and has no authority to certify code, tests or refinements. It does not import Charloom
or perform NL-to-contract conversion. Runtime dependency: Lark 1.3.1.

Run from this directory:

```
python -m pytest tests -q
```

Before any normative use: reconcile all G-00 original clauses, add V0 externally,
prove core preservation properties for a fixed syntax/version, implement Markdown
block extraction, AST provenance for derived nodes, imports and bounded quantifiers,
and complete the real guardian/domain contracts. `source_cut` must be supplied by
trusted source acquisition. A parser success only means a structural candidate exists.
