# Contributing

Thank you for considering a contribution to this security research collection.

## What belongs here

- **Educational case studies** — sanitized, reproducible vulnerability walk-throughs.
- **Audit methodology notes** — checklists, severity reasoning, tooling tips.
- **Report templates** — clean, reusable structures following the repo's format.
- **Public disclosures** — only with explicit authorization (see below).

## What does NOT belong here

- Private client findings before public disclosure or written approval.
- Weaponized exploits, live PoCs against mainnet contracts, or anything violating
  a bug bounty program's terms.
- Unverified "vulnerabilities" without a reproduction or clear reasoning chain.

## Report format

New reports follow the numbered convention `NNN-short-slug.md` and must include:

1. **Classification** — educational / client-approved / contest-based / independent research.
2. **Affected component** — commit/branch reference where applicable.
3. **Description** — root cause, not just the symptom.
4. **Impact** — argued severity with reasoning in both directions
   (why not higher, why not N/A).
5. **Remediation** — narrow fix, plus how it was verified.

## Process

1. Open an issue describing the proposed addition.
2. Fork, branch (`docs/my-topic`), and commit following the format above.
3. Open a pull request — maintainers review for accuracy and sanitization.

By contributing, you agree your content is licensed under the repository's MIT license.
