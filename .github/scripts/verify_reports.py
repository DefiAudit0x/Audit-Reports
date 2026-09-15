#!/usr/bin/env python3
"""CI gate for the Audit-Reports repository.

Turns the report index and the report files themselves into checked
invariants:

1. INDEX <-> FILES (bidirectional) — every completed row in the README index
   links a report file that exists, and every report file on disk appears in
   the index with the exact same filename.

2. NUMBERING — reports are numbered 001..N sequentially with no gaps; teaser
   rows ("coming soon") are ignored.

3. TEMPLATE — each report carries the sections the repository's own
   templates/report-template.md defines (Summary, Threat model, Violated
   invariant, Impact, Proof of Concept / Reproduction, Remediation,
   Regression / Verification, References), accepting both the numbered
   ("## 3. Threat model") and legacy ("## Threat model") heading styles.

4. SANITY — a report file must be non-trivial (>= 1000 chars) and must not
   be a leftover empty placeholder.

Usage: verify_reports.py [repo_root]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MIN_LENGTH = 1000

# Section titles required in every report; both "## N. Title" (template)
# and "## Title" (legacy) heading styles are accepted.
REQUIRED_SECTIONS: list[tuple[str, str]] = [
    ("summary", r"##\s*(?:\d+\.\s*)?Summary|##\s*(?:\d+\.\s*)?Executive summary"),
    ("threat model", r"##\s*(?:\d+\.\s*)?Threat model"),
    ("violated invariant", r"##\s*(?:\d+\.\s*)?Violated invariant"),
    ("impact", r"##\s*(?:\d+\.\s*)?Impact"),
    ("poc / reproduction", r"##\s*(?:\d+\.\s*)?Proof of Concept|##\s*(?:\d+\.\s*)?Reproduction(?! outline)|##\s*(?:\d+\.\s*)?Reproduction outline|##\s*(?:\d+\.\s*)?Minimal reproduction"),
    ("remediation", r"##\s*(?:\d+\.\s*)?Remediation"),
    ("regression / verification", r"##\s*(?:\d+\.\s*)?Regression test|##\s*(?:\d+\.\s*)?Verification"),
    ("references", r"##\s*(?:\d+\.\s*)?References"),
]


def main(repo_root: Path) -> int:
    readme_path = repo_root / "README.md"
    if not readme_path.is_file():
        print(f"FAIL: README.md not found at {readme_path}")
        return 1
    readme = readme_path.read_text(encoding="utf-8")

    failures: list[str] = []

    # --- 1. Parse completed index rows: | NNN | [title](./file.md) | ... | ---
    row_re = re.compile(r"^\|\s*(\d{3})\s*\|\s*\[[^\]]*\]\(\./([^)]+\.md)\)", re.M)
    indexed: dict[str, str] = {}
    for num, fname in row_re.findall(readme):
        if num in indexed and indexed[num] != fname:
            failures.append(f"index lists #{num} twice with different files")
        indexed[num] = fname

    # --- Reports on disk (root-level NNN-*.md only; templates/ excluded). ---
    disk: dict[str, str] = {
        p.name[:3]: p.name for p in repo_root.glob("0*.md") if p.is_file()
    }

    # --- 1a. Index rows must point at existing files. ---
    for num, fname in sorted(indexed.items()):
        if not (repo_root / fname).is_file():
            failures.append(f"index row #{num} links a missing file: {fname}")

    # --- 1b. Disk reports must be indexed, with matching filenames. ---
    for num, fname in sorted(disk.items()):
        if num not in indexed:
            failures.append(f"{fname} exists but is not in the README index")
        elif indexed[num] != fname:
            failures.append(
                f"index #{num} links {indexed[num]} but the file on disk is {fname}"
            )

    # --- 2. Sequential numbering. ---
    numbers = sorted(disk)
    expected = [f"{i:03d}" for i in range(1, len(numbers) + 1)]
    if numbers != expected:
        failures.append(f"report numbering is not sequential 001..N: found {numbers}")

    # --- 3 + 4. Template sections and sanity per report. ---
    for fname in sorted(p.name for p in repo_root.glob("0*.md")):
        text = (repo_root / fname).read_text(encoding="utf-8")
        if len(text) < MIN_LENGTH:
            failures.append(f"{fname}: suspiciously short ({len(text)} chars)")
            continue
        for label, pattern in REQUIRED_SECTIONS:
            if not re.search(pattern, text, re.IGNORECASE):
                failures.append(f"{fname}: missing required section '{label}'")

    # --- Report. ---
    print(f"Checked {len(disk)} reports against the README index.")
    if failures:
        print(f"RESULT: FAIL — {len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS — index, numbering, template sections, and links all verified.")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    sys.exit(main(root))
