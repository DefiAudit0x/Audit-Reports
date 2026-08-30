# Report {NNN}: {Vulnerability Title}

| Field | Value |
| --- | --- |
| **Type** | Educational case study / Independent research / Contest-based / Client-approved |
| **Status** | Draft / Complete |
| **Date** | YYYY-MM-DD |
| **Language** | Solidity `^0.8.x` |
| **Severity** | Critical / High / Medium / Low / Informational (see [severity matrix](./severity-matrix.md)) |
| **Repository** | [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) or external |

---

## 1. Summary

Two to four sentences: what breaks, where, and why it matters. State explicitly whether this
targets a real protocol or an educational fixture.

## 2. Background

Brief context on the contract or protocol: purpose, architecture, and the component under
review. Include only what a reader needs to understand the finding.

## 3. Threat model

- **Asset at risk:** what can be lost or corrupted (funds, control, availability).
- **Privileged actors:** who holds special rights (owner, pauser, oracle, sequencer).
- **Untrusted actors:** who can trigger the path (any user, specific roles, external dependency).
- **Preconditions:** state, timing, capital, or configuration required before exploitation.

## 4. Violated invariant

> State the invariant in one sentence, as a property the protocol must always hold.

Explain why the vulnerable code violates it.

## 5. Impact

Worst-case outcome under realistic conditions. Quantify where possible (percentage of funds,
DoS duration, affected functions). Note any mitigating factors honestly — do not overstate.

## 6. Technical details

Walk through the execution path step by step. Quote the relevant code with file and line
references:

```solidity
// VulnerableContract.sol, L42-L47
function withdraw(address token) external {
    require(tx.origin == owner);   // authorization coupled to the outer EOA
    ...
}
```

## 7. Proof of Concept

A minimal, self-contained Foundry test. PoCs must be educational: they demonstrate the bug in
a local test environment and must not include weaponized tooling, live addresses, or operational
attack infrastructure.

```solidity
// test/Poc.t.sol
function testExploit() public { ... }
```

Run with:

```bash
forge test --match-test testExploit -vv
```

## 8. Remediation

The narrowest correct fix. Show a diff or the corrected code, and explain why the fix restores
the invariant without introducing new issues.

## 9. Regression test

A test that re-runs the exploit against the fixed code and asserts it now fails:

```solidity
function testCannotExploitAfterFix() public { ... }
```

## 10. References

- Similar public findings, post-mortems, or write-ups
- Relevant standards (SWC IDs, ERC specifications, Chainlink documentation)
- Tool output that surfaces the issue (Slither detector name, forge fuzz seed)

---

**Author:** @DefiAudit0x · **Reviewed:** YYYY-MM-DD · **Disclosure:** educational / approved
