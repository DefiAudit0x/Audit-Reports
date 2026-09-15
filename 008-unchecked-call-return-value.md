# Report 008: Unchecked Low-Level Call Return Value

| Field | Value |
| --- | --- |
| **Type** | Educational case study |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Medium (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | Educational fixture, pattern from [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) |

---

## 1. Summary

A payout pool deletes a user's claim from accounting, sends the ether with a raw `call`, and never inspects the returned success flag. When the recipient is a contract whose `receive` reverts, the sub-call fails silently — the outer transaction completes, the claim is destroyed, and the ether was never delivered. Accounting and reality diverge in one transaction. Educational case study on a fixture pool.

## 2. Background

The vulnerable claim path:

```solidity
// PayoutPool.sol, L40-L48
function claim(uint256 id) external {
    Claim storage c = claims[id];
    require(c.payee != address(0), "no claim");

    uint256 amount = c.amount;
    delete claims[id];                                // accounting advances first

    (bool ok, ) = c.payee.call{value: amount}("");    // ok is assigned...
    // ...and never inspected                          // ...but never checked
}
```

The `checks-effects-interactions` ordering is actually correct for reentrancy — the deletion happens before the external call. The single defect is the ignored `ok`: a reverted callee does not propagate through a raw `call`, it just returns `false`.

## 3. Threat model

- **Asset at risk:** claimants' payouts — destroyed claims whose ether strands inside the pool.
- **Privileged actors:** none required for the failure; administrators only matter for recovery.
- **Untrusted actors:** any payee that is (or can register) a contract with a reverting `receive` — including a hostile attacker registering a reverting contract to grief the pool's solvency accounting.
- **Preconditions:** at least one payee that is a contract rather than an EOA.

## 4. Violated invariant

> Protocol accounting may advance only after the value transfer it records has verifiably succeeded.

Deleting the claim before confirming the transfer breaks this permanently — there is no code path that restores the claim or the ether.

## 5. Impact

The claimant loses the ability to ever receive their payout: `claims[id]` is gone, the pool keeps the ether, and if the pool treats undelivered balances as treasury residue, the value is captured rather than merely frozen. For payroll-style systems the failure mode is worse in a different direction: the recipient is marked *paid* in the accounting while having received nothing, poisoning every downstream reconciliation.

Argued in both directions: for plain EOAs the bug can never trigger — an EOA's receive cannot fail — so a deployment whose payees are vetted EOAs never observes it. The moment any payee is a contract (multisigs and smart wallets are the norm), the failure is reachable by accident, and by malice the reverting-receiver is a one-line contract. Severity for this fixture: **Medium** — value loss and accounting corruption, gated on recipient type.

## 6. Technical details

Failure trace:

```text
1. claimant (a contract with reverting receive) is owed 1 ether
2. anyone calls claim(id):
     a. claim record deleted        — storage change commits
     b. call{value: 1 ether}        — sub-call reverts, returns ok = false
     c. execution continues         — nothing throws
3. final state: claim gone, ether still in pool, no error surfaced anywhere
```

The same class covers the ERC-20 variant: `token.call(abi.encodeWithSelector(TRANSFER, ...))` with neither the boolean nor the return data inspected, which silently accepts a reverting token transfer. Every external call site needs exactly one of: a checked high-level call, a `require` on the boolean, or explicit `try/catch` with defined recovery.

## 7. Proof of Concept

```solidity
// test/UncheckedCall.t.sol (educational sketch)
contract RevertingReceiver {
    receive() external payable { revert("no"); }
}

function testClaimVanishesWhenPayeeReverts() public {
    RevertingReceiver r = new RevertingReceiver();
    pool.register(address(r), 1 ether);

    pool.claim(0);                          // completes "successfully"

    vm.expectRevert("no claim");
    pool.claim(0);                          // claim is gone...
    assertEq(address(r).balance, 0 ether);  // ...but was never paid
    assertEq(address(pool).balance, 1 ether); // ether stranded in the pool
}
```

Run with:

```bash
forge test --match-test testClaimVanishesWhenPayeeReverts -vv
```

## 8. Remediation

The narrowest correct fix is one line:

```diff
  (bool ok, ) = c.payee.call{value: amount}("");
+ require(ok, "payout failed");
```

For better liveness, prefer pull-over-push: `claim()` marks the payout claimable and the payee invokes `withdraw()` themselves, so a reverting receive only harms its own owner. A middle option is `try/catch` that restores the claim on failure:

```solidity
try c.payee.call{value: amount}("") { /* delivered */ }
catch { claims[id] = c; }   // restore for later retry
```

Keep the delete-before-call ordering in all variants — it is the correct reentrancy posture.

## 9. Regression test

```solidity
function testClaimRestoredWhenPayeeReverts() public {
    RevertingReceiver r = new RevertingReceiver();
    pool.register(address(r), 1 ether);

    vm.expectRevert("payout failed");       // failure is now loud
    pool.claim(0);

    Claim memory c = pool.claims(0);        // claim survives for retry
    assertEq(c.amount, 1 ether);
}
```

## 10. References

- SWC-104 — Unchecked Call Return Value.
- Solidity documentation — error handling semantics of low-level `call`.
- OpenZeppelin `Address.sendValue` — checked ETH transfer helper.
- ConsenSys Smart Contract Best Practices — "always handle errors from external calls".
