<div align="center">

# DefiAudit Security Reports

**Public smart-contract security research, educational case studies, and sanitized audit material.**

[![License: MIT](https://img.shields.io/badge/License-MIT-181717?style=flat-square)](LICENSE)
[![Reports](https://img.shields.io/badge/Reports-3+-blue?style=flat-square)](#report-index)
[![Foundry](https://img.shields.io/badge/Tested%20with-Foundry-FF8C42?style=flat-square)](https://getfoundry.sh)
[![Slither](https://img.shields.io/badge/Static%20Analysis-Slither-1F4E79?style=flat-square)](https://github.com/crytic/slither)

</div>

---

> ⚠️ **Disclaimer:** Nothing in this repository should be interpreted as a guarantee that a protocol is secure. All reports are labeled by their source and scope.

## Report index

| # | Report | Type | Severity | Status |
| --- | --- | --- | ---: | --- |
| 001 | [Reentrancy Demo](./001-reentrancy-demo.md) | Educational case study | High | ✅ Complete |
| 002 | [tx.origin Authorization Bypass](./002-tx-origin-access-control.md) | Educational case study | High | ✅ Complete |
| 003 | [Stale Oracle Data](./003-stale-oracle.md) | Educational case study | Context-dependent | ✅ Complete |
| 004 | `_coming soon_` — Flash Loan Price Manipulation | Independent research | High | 🚧 In progress |
| 005 | `_coming soon_` — Privileged Mint via Access Control Flaw | Independent research | Critical | 📋 Planned |

## Audit methodology

The review process follows a structured pipeline:

1. **Scope & trust boundaries** — Identify privileged actors, external dependencies, and assets at risk.
2. **Invariants & assumptions** — Document protocol invariants and threat model before code review.
3. **Manual review** — Trace privileged flows, accounting, external calls, oracle dependencies, and upgrade paths.
4. **Static analysis** — Run Slither and complementary tooling. Treat all tool output as a lead, not a finding.
5. **Reproduction** — Reproduce material findings with a minimal Foundry test or PoC.
6. **Impact analysis** — Describe exploitability and impact precisely, without overstating claims.
7. **Remediation** — Propose a narrow fix and verify it with regression tests.

### Primary tools

`Foundry` · `Slither` · `Hardhat` · `Echidna` (where applicable) · `Python` (custom analysis)

## Report policy

| Report type | Disclosure |
| --- | --- |
| **Client-approved** | Sanitized to remove private information, credentials, sensitive addresses, and weaponized exploit details. Published only with explicit authorization. |
| **Contest-based** | Sourced from public audit contests (Code4rena, Sherlock, Cantina). The contest handle is identified, and the scope is documented. |
| **Educational** | Original, self-authored examples designed to teach a specific vulnerability class. No production protocol is described. |
| **Independent research** | Public post-mortems of real incidents, written from public on-chain data and disclosed reports. No private information is used. |

## Repository structure

```
.
├── 001-reentrancy-demo.md
├── 002-tx-origin-access-control.md
├── 003-stale-oracle.md
├── templates/
│   ├── report-template.md       # standard report template
│   └── severity-matrix.md       # severity rubric
├── LICENSE
└── README.md
```

## Contributing

This repository is primarily a personal research archive. If you spot an error in a report or want to suggest an improvement:

1. Open an [issue](../../issues) describing the discrepancy.
2. Reference the report number (`001`, `002`, …) and the specific claim you believe is incorrect.
3. Provide a source (Code4rena report, Etherscan tx, Slither output) supporting your correction.

## Contact

For security research, collaboration, or audit inquiries:

- X: [@DeFiAudit](https://x.com/DeFiAudit)
- Telegram: [@DefiAudit0x](https://t.me/DefiAudit0x)
- Email: [defiaudit@gmail.com](mailto:defiaudit@gmail.com)

## License

[MIT](./LICENSE) — Educational and research material. Weaponized exploit code is intentionally omitted.
