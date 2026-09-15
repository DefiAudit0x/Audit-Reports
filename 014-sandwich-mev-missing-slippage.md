# Report 014: Sandwich MEV via Missing Slippage Protection

| Field | Value |
| --- | --- |
| **Type** | Educational case study |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Medium (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | [evm-audit-lab — Lab 06](https://github.com/DefiAudit0x/evm-audit-lab) (runnable PoC) |

---

## 1. Summary

An AMM's `swap()` executes at whatever price is live when the transaction lands and accepts no slippage bound and no deadline. Any swap sitting in the mempool can be sandwiched: a searcher front-runs it with a large same-direction swap (moving the price), lets the victim trade at the moved price, then back-runs to restore it — pocketing the difference as extracted slippage. The victim's loss equals the attacker's profit minus pool fees, and it happens to every unbounded swap that is visible before inclusion.

## 2. Background

The vulnerable swap (condensed from [Lab 06](https://github.com/DefiAudit0x/evm-audit-lab)):

```solidity
// VulnerableAmm.sol
function swap(uint256 amountIn, bool zeroForOne) external returns (uint256 out) {
    out = getAmountOut(amountIn, ...);          // price is whatever is live NOW
    // ... token transfers ...
    // no minAmountOut, no deadline — the caller signed nothing about price
}
```

The user's *intent* (a price they saw when signing) never reaches the contract, so the contract cannot defend it.

## 3. Threat model

- **Asset at risk:** the swapper's expected output — value extracted as slippage, bounded by pool depth and the victim's transaction size.
- **Privileged actors:** none needed; the attacker is any searcher with ordering ability (priority fees, bundles).
- **Untrusted actors:** whoever can observe the mempool and order transactions around the victim's — which on public chains is everyone.
- **Preconditions:** the victim's transaction is visible before inclusion and their swap carries no on-chain slippage bound.

## 4. Violated invariant

> A trader receives the price they expected when they signed.

With no `minAmountOut` and no `deadline`, the executed price is fully controlled by whoever orders the transactions around it.

## 5. Impact

The lab's worked example (pool seeded 100 A / 100 B, victim swapping 10 A for B):

```text
fair execution:          victim receives ~9.07 B

attacker front-runs:     swaps 50 A -> 33.27 B        (price of B rises)
victim lands:            receives ~4.16 B             (-4.9 B vs fair)
attacker back-runs:      sells 33.27 B -> ~55.42 A

net: attacker +5.42 A, victim -4.9 B — extracted slippage, twice the pool fee
```

Argued in both directions: for tiny trades in deep pools the extracted slippage is dust, and a searcher may not bother — impact collapses toward Informational. But the loss scales with trade size and pool shallowness, requires no bug in the pool's math, and repeats on every visible unbounded swap; on chains with mature MEV infrastructure it is close to automatic. Standard audit practice rates a missing slippage parameter **Medium** — a direct, quantifiable user loss that the protocol could have prevented with one parameter.

## 6. Technical details

Why the sandwich is risk-free for the attacker: the front-run *moves the price in the direction the victim is already trading*, so the victim's own transaction executes the attacker's exit at the inflated price. The attacker's round trip pays the pool fee twice, which is why tiny victim trades are not worth attacking — the victim's extracted slippage must exceed two fees plus the bundle's priority cost.

The missing-deadline half matters separately: a swap signed hours before inclusion remains executable against any future market state, so even a reasonable `minAmountOut` goes stale and turns into a free option for the counterparty (the classic "stale order" MEV).

## 7. Proof of Concept

Runnable in [Lab 06](https://github.com/DefiAudit0x/evm-audit-lab):

```bash
git clone https://github.com/DefiAudit0x/evm-audit-lab && cd evm-audit-lab
forge test --match-contract SandwichTest -vvv
```

Core assertion (condensed from `test/Sandwich.t.sol`):

```solidity
// Front-run: attacker swaps 50 A -> B before the victim lands.
vm.prank(attacker);
vulnerable.swap(50e18, true);

// Victim lands at the moved price: ~4.16 B instead of the fair ~9.07 B.
vm.prank(victim);
uint256 out = vulnerable.swap(10e18, true);
assertApproxEqAbs(out, 4.16e18, 0.01e18);

// Back-run: attacker closes for ~55.42 A — a net +5.42 A profit.
vm.prank(attacker);
uint256 closed = vulnerable.swap(33.27e18, false);
assertGt(closed, 55e18);
```

## 8. Remediation

Add the two parameters the victim's intent needs to be enforceable:

```diff
- function swap(uint256 amountIn, bool zeroForOne) external returns (uint256 out) {
+ function swap(uint256 amountIn, uint256 minAmountOut, uint64 deadline, bool zeroForOne)
+     external returns (uint256 out) {
+     require(block.timestamp <= deadline, "expired");
      out = getAmountOut(...);
+     require(out >= minAmountOut, "slippage");
```

The front-run now makes the victim's transaction *revert* instead of executing at a bad price, and the attacker's round trip pays two fees for nothing. Wallets and routers must surface both parameters honestly (this is where the protection usually breaks in practice).

## 9. Regression test

```solidity
function testSandwichFailsAgainstSlippageBound() public {
    vm.prank(attacker);
    safe.swap(50e18, 1, block.timestamp, true);          // attacker moves price

    vm.prank(victim);
    vm.expectRevert("slippage");                          // victim reverts, keeps funds
    safe.swap(10e18, 9e18, block.timestamp, true);

    vm.prank(attacker);
    vm.expectRevert("expired");                           // stale orders are not free options
    safe.swap(33.27e18, 1, block.timestamp - 1, false);
}
```

## 10. References

- Uniswap V2 interface — the canonical `amountOutMin` / `deadline` parameters.
- Ethereum.org — MEV: front-running, sandwich attacks, priority fees.
- Flash Boys 2.0 (Daian et al., 2019) — the original sandwich/MEV study.
- SWC-114 — Transaction Order Dependence.
