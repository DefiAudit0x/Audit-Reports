<div align="center">

# DefiAudit Security Reports

**Public smart-contract security research, educational case studies, and sanitized audit material.**

[![License: MIT](https://img.shields.io/badge/License-MIT-181717?style=flat-square)](LICENSE)
[![Reports](https://img.shields.io/badge/Reports-14+-blue?style=flat-square)](#report-index)
[![Foundry](https://img.shields.io/badge/Tested%20with-Foundry-FF8C42?style=flat-square)](https://getfoundry.sh)
[![Slither](https://img.shields.io/badge/Static%20Analysis-Slither-1F4E79?style=flat-square)](https://github.com/crytic/slither)
[![Verify Reports](https://github.com/DefiAudit0x/Audit-Reports/actions/workflows/verify-reports.yml/badge.svg)](../../actions/workflows/verify-reports.yml)

</div>

---

> ⚠️ **Disclaimer:** Nothing in this repository should be interpreted as a guarantee that a protocol is secure. All reports are labeled by their source and scope.

## Report index

| # | Report | Type | Severity | Status |
| --- | --- | --- | ---: | --- |
| 001 | [Reentrancy Demo](./001-reentrancy-demo.md) | Educational case study | High | ✅ Complete |
| 002 | [tx.origin Authorization Bypass](./002-tx-origin-access-control.md) | Educational case study | High | ✅ Complete |
| 003 | [Stale Oracle Data](./003-stale-oracle.md) | Educational case study | Context-dependent | ✅ Complete |
| 004 | [Flash Loan Price Manipulation](./004-flash-loan-price-manipulation.md) | Independent research | High | ✅ Complete |
| 005 | [Privileged Mint via Access Control Flaw](./005-privileged-mint-access-control.md) | Independent research | Critical | ✅ Complete |
| 006 | [ERC-4626 First-Depositor Inflation Attack](./006-erc4626-inflation-attack.md) | Educational case study | Medium | ✅ Complete |
| 007 | [Rounding Direction Errors in Liquidity Math](./007-rounding-direction-liquidity-math.md) | Educational case study | Low | ✅ Complete |
| 008 | [Unchecked Low-Level Call Return Value](./008-unchecked-call-return-value.md) | Educational case study | Medium | ✅ Complete |
| 009 | [EIP-712 Signature Replay Across Chains and Nonces](./009-eip712-signature-replay.md) | Independent research | High | ✅ Complete |
| 010 | [Uninitialized UUPS Proxy Takeover](./010-unprotected-uups-initializer.md) | Independent research | Critical | ✅ Complete |
| 011 | [Unbounded Loop Denial of Service](./011-unbounded-loop-dos.md) | Educational case study | Medium | ✅ Complete |
| 012 | [Fee-on-Transfer Token Accounting Break](./012-fee-on-transfer-accounting.md) | Educational case study | Medium | ✅ Complete |
| 013 | [Storage Layout Collisions in Upgradeable Proxies](./013-storage-layout-collision-upgrades.md) | Educational case study | Critical | ✅ Complete |
| 014 | [Sandwich MEV via Missing Slippage Protection](./014-sandwich-mev-missing-slippage.md) | Educational case study | Medium | ✅ Complete |
| 015 | `_coming soon_` — Cross-Chain Message Replay | Independent research | High | 📋 Planned |

## Lab cross-reference

Most reports are backed by a runnable Foundry lab (vulnerable + remediated contracts, exploit and regression tests) in [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab):

| Report | Lab | Runnable PoC |
| --- | --- | --- |
| 001 — Reentrancy Demo | [lab-01-reentrancy](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-01-reentrancy) | `forge test --match-contract ReentrancyTest` |
| 002 — tx.origin Authorization Bypass | [lab-02-tx-origin](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-02-tx-origin) | `forge test --match-contract TxOriginTest` |
| 003 — Stale Oracle Data | [lab-04-oracle-manipulation](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-04-oracle-manipulation) | `forge test --match-contract StaleOracleTest` |
| 004 — Flash Loan Price Manipulation | [lab-03-flash-loan](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-03-flash-loan) | `forge test --match-contract FlashLoanTest` |
| 005 — Privileged Mint via Access Control Flaw | [lab-09-privileged-mint](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-09-privileged-mint) | `forge test --match-contract PrivilegedMintTest` |
| 006 — ERC-4626 First-Depositor Inflation Attack | [lab-11-erc4626-inflation](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-11-erc4626-inflation) | `forge test --match-contract InflationAttackTest` |
| 007 — Rounding Direction Errors in Liquidity Math | [lab-05-integer-precision-loss](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-05-integer-precision-loss) | `forge test --match-contract PrecisionTest` |
| 008 — Unchecked Low-Level Call Return Value | [lab-10-unchecked-return-value](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-10-unchecked-return-value) | `forge test --match-contract UncheckedReturnTest` |
| 009 — EIP-712 Signature Replay | [lab-08-signature-replay](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-08-signature-replay) | `forge test --match-contract SignatureReplayTest` |
| 010 — Uninitialized UUPS Proxy Takeover | [lab-14-uups-initializer](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-14-uups-initializer) | `forge test --match-contract UupsTakeoverTest` |
| 011 — Unbounded Loop Denial of Service | [lab-12-loop-dos](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-12-loop-dos) | `forge test --match-contract LoopDoSTest` |
| 012 — Fee-on-Transfer Token Accounting Break | [lab-13-fee-on-transfer](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-13-fee-on-transfer) | `forge test --match-contract FeeOnTransferTest` |
| 013 — Storage Layout Collisions in Upgrades | [lab-07-proxy-storage-collision](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-07-proxy-storage-collision) | `forge test --match-contract ProxyCollisionTest` |
| 014 — Sandwich MEV via Missing Slippage Protection | [lab-06-sandwich-mev](https://github.com/DefiAudit0x/evm-audit-lab/tree/main/labs/lab-06-sandwich-mev) | `forge test --match-contract SandwichTest` |

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
