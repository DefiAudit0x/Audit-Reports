# DefiAudit Security Reports



Public smart-contract security research, educational case studies, and sanitized audit material by **DefiAudit**.



> Reports are labeled clearly as educational, contest-based, independent research, or client-approved sanitized material. Nothing in this repository should be interpreted as a guarantee that a protocol is secure.
> 


## Report index



| Report | Type | Severity | Status |

|---|---|---:|---|

| [001 — Reentrancy Demo](001-reentrancy-demo.md) | Educational case study | High | Complete |

| [002 — `tx.origin` Authorization Bypass](002-tx-origin-access-control.md) | Educational case study | High | Complete |

| [003 — Stale Oracle Data](003-stale-oracle.md) | Educational case study | Context-dependent | Complete |



## Audit methodology



The review process starts with scope, trust boundaries, assumptions, and invariants. It then combines manual business-logic review with targeted static analysis and reproducible tests. Findings are documented with affected code, impact, exploit preconditions, a minimal proof of concept or regression test, remediation, and retest status.



The primary tools are Foundry, Slither, Hardhat, and custom Solidity or Python utilities where appropriate. Tool output is treated as a lead for manual verification, not as a substitute for reasoning about protocol behavior.



## Report policy



Client reports are published only with permission and are sanitized to remove private information, credentials, sensitive addresses, and weaponized exploit details. Contest and independent research reports identify their source and scope explicitly.



## Contact



For security research or collaboration, contact [@DefiAudit on X](https://x.com/DefiAudit) or [@DefiAudit0x on Telegram](https://t.me/DefiAudit0x).


