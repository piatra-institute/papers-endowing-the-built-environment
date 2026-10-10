# Audit

## 2026-10-10 — First locally completed edition

Scope: full financing argument, illustrative lifecycle study and substantial
institutional second half. Research/provenance, ten CSL references, manuscript,
locked executable model, results, figure and version-bound reviews are included.

The launch account charges the retained apartments their foregone sale value.
All treatments start with equal dedicated capital and identical obligations.
An ordinary reserve holding the financial endowment's portfolio is exactly
equivalent. Arrears, overdue work, terminal continuation and authorized rescue
policies remain visible. Institutional proposals are distinguished from
computational findings; legal comparisons retain source dates and scope.

Verification performed:

- `simulation/.venv/bin/python -B -m unittest discover -s simulation -p 'test_*.py' -v`, from the paper root: 12/12 pass.
- Full recorded `renewal` suite: all required experiments PASS. Exact command is in `simulation/README.md`; receipt hashes/runtime are in `verification/renewal.json`.
- Fresh same-environment execution in an isolated temporary copy: `cmp` confirms byte-identical results.json and complete annual.json ledgers.
- `python3 tooling/papers.py refs endowing-the-built-environment`: all 10 cited IDs resolve. Primary support and limitations are recorded in sources.md.
- `python3 tooling/papers.py claims endowing-the-built-environment`: 72 bound entries and required execution PASS.
- `python3 tooling/papers.py voice endowing-the-built-environment` and `lint`: advisory checks complete; 11 contrast candidates and the rhythm warning reviewed, with useful assumption/scope distinctions retained.
- `python3 2026/10/endowing-the-built-environment/build.py`: PASS, 15 pages; final log has no warning/missing-character matches.
- Rendered every page at 115 dpi with `pdftoppm` and visually inspected it. Legal short titles and Romanian diacritics were improved; the three affected pages were reinspected, while all other final page images remained byte-identical.
- `python3 tooling/papers.py check endowing-the-built-environment --stage local --json`: PASS. Exact report in `verification/local-check.json`.

Shared tooling: all 43 tests pass under
`PYTHONPATH=tooling python3 -B -m unittest discover -s tooling/tests -v`.
Scaffold/pipeline changes support the actual local evidence/review contract and
keep publication separate. Unrelated tooling README changes were preserved.
Scoped changed-file whitespace checks pass. The full tooling diff check reports
only pre-existing Markdown hard-break whitespace in README.md:16, left untouched.
A credential-pattern scan of the deliverable files found no matches.

Build logs/manifests, renders, virtual environments and seed chats stay out of Git.
No commit, push, GitHub repository creation or website update was performed.
The findings are conditional illustrations, not market forecasts, engineering
certification, qualified legal advice or an externally reviewed business case.
