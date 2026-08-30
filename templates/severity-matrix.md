# Severity Matrix

Ratings follow impact x likelihood practice used in public audit contests (Code4rena,
Sherlock, Cantina), adapted for educational and independent-research reports.

| Severity | Impact | Likelihood | Typical examples |
| --- | --- | --- | --- |
| **Critical** | Direct, unbounded loss of protocol funds or irreversible governance takeover | High — any unprivileged actor, no special preconditions | Unauthorized mint; vault drain via reentrancy with no entry guard |
| **High** | Material fund loss or protocol insolvency under realistic conditions | Medium-High — one realistic precondition (stale oracle, key misuse) | Stale-oracle collateral valuation; `tx.origin` authorization bypass |
| **Medium** | Limited loss, temporary DoS of core functions, or accounting drift recoverable only by admin | Medium — requires specific state, timing, or capital | Unchecked low-level call bricking withdrawals; unbounded loop griefing |
| **Low** | Inconvenience, gas waste, or weakened invariant without direct loss | Low-Medium | Timestamp-dependent gating in a narrow window; missing event on state change |
| **Informational** | Code quality, documentation, or maintainability observations | Not applicable | NatSpec gaps; variable shadowing; magic numbers |

## Rating procedure

1. **State the violated invariant** and the worst-case state reachable by the attacker.
2. **Bound exploitability:** who can trigger it, capital required, single-block versus
   multi-block attack, proxy/upgradeability caveats.
3. **Match the row:** choose the highest severity whose impact and likelihood both fit.
4. **Document the deciding factor** when two severities are close — the reasoning must be
   visible to the reader.

## Context flags

| Flag | Meaning |
| --- | --- |
| **Context-dependent** | Severity depends on deployment assumptions; the assumptions must be stated in the report. |
| **Contest-based** | Where the source contest published a severity, align with it and note disagreements explicitly. |
| **Client-approved** | Sanitized report; severity reflects the original engagement unless redaction changes context. |

> Reports in this repository are educational or research artifacts. Severity describes
> theoretical impact in the described scope and is not a security guarantee for any live system.
