# Report 007: Rounding Direction Errors in Liquidity Math

| Field | Value |
| --- | --- |
| **Type** | Educational case study |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Low standalone — escalates when composed (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | Educational fixture, pattern from [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) |

---

## 1. Summary

A liquidity pool computes deposit shares with ceiling division and computes redemption amounts with ceiling division too — both round in the transactor's favor. Every deposit-withdraw cycle leaks a wei-scale unit out of the shared pool and into the caller's pocket. A single leak is dust; a batched loop of self-transfers, or composition with share-price manipulation, turns the same defect into a measurable drain. Educational case study on a fixture pool.

## 2. Background

Share math in the fixture:

```solidity
// RoundedPool.sol, L24-L33
function deposit(uint256 assets) external returns (uint256 shares) {
    shares = _ceilDiv(assets * totalShares, totalLiquidity);  // rounds UP — favors depositor
    totalShares   += shares;
    totalLiquidity += assets;
    // ...
}

function withdraw(uint256 shares) external returns (uint256 assets) {
    assets = _ceilDiv(shares * totalLiquidity, totalShares);  // rounds UP again — favors withdrawer
    // ...
}

function _ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
    return (a + b - 1) / b;
}
```

Both rounding points push the error in the same direction: toward the user, at the pool's expense.

## 3. Threat model

- **Asset at risk:** shared pool liquidity — one rounding unit per operation by default.
- **Privileged actors:** none required.
- **Untrusted actors:** any liquidity provider, including contracts that batch many operations per transaction.
- **Preconditions:** none; profitability requires either free internal batching or an inflated share price (composition with report [006](./006-erc4626-inflation-attack.md)).

## 4. Violated invariant

> Rounding must be applied in a single, protocol-favoring direction — the same operation must never round in the user's favor on the way in and again on the way out.

Ceiling division at both ends violates this: the pool pays the rounding error twice per deposit-redemption cycle, and the user collects it twice.

## 5. Impact

Baseline: 1 wei of value per operation. In the naive attack — deposit 1 wei-equivalent and redeem in the same transaction — the pool loses a rounding unit while the attacker pays only gas; at typical mainnet prices this loses money, which is why the standalone rating is **Low**.

Argued in both directions, the ceiling case: when `totalShares` is tiny and `totalLiquidity` is large, one rounding unit of shares corresponds to a large amount of assets — the same degenerate-supply regime exploited in [006](./006-erc4626-inflation-attack.md). A batch contract performing millions of deposit-redeem pairs inside a single transaction multiplies the per-unit leak without per-operation gas overhead. Under those compositions the defect behaves as High; on its own, with mature supply and per-transaction gas floors, it is dust. Rating for this report: **Low**.

## 6. Technical details

Round-trip walkthrough:

```text
1. pool has totalShares = S, totalLiquidity = L
2. attacker deposits a tiny amount a:
     shares = ceil(a * S / L)  → at least 1 wei, possibly a "free" extra unit
3. attacker immediately withdraws those shares:
     assets = ceil(shares * L / S) → rounds back up in the attacker's favor
4. net position: zero shares, assets ≥ a + rounding units, pool liquidity decreased by the difference
```

The defect class is *symmetric upward rounding*: each division is individually defensible ("don't shortchange the user"), but the pair is only safe when at most one side rounds toward the user.

## 7. Proof of Concept

```solidity
// test/RoundingDrain.t.sol (educational sketch)
function testRoundingLeaksPoolValue() public {
    uint256 liqBefore = pool.totalLiquidity();
    vm.startPrank(attacker);
    for (uint256 i; i < 1_000; ++i) {     // a batch contract can push this far higher
        uint256 s = pool.deposit(1 wei);
        pool.withdraw(s);
    }
    vm.stopPrank();
    assertLt(pool.totalLiquidity(), liqBefore);  // pool lost value to rounding alone
}
```

Run with:

```bash
forge test --match-test testRoundingLeaksPoolValue -vv
```

## 8. Remediation

Fix the rounding direction once, in both places:

```diff
- shares = _ceilDiv(assets * totalShares, totalLiquidity);
+ shares = (assets * totalShares) / totalLiquidity;          // floor — pool favored on mint
- assets = _ceilDiv(shares * totalLiquidity, totalShares);
+ assets = (shares * totalLiquidity) / totalShares;          // floor — pool favored on redeem
```

Use `mulDiv` (OpenZeppelin / Solady) for full-precision intermediate products. Add virtual share/asset offsets as in the ERC-4626 pattern so tiny supply cannot make a rounding unit valuable. Finally, add a stateful fuzz invariant asserting that a matched deposit-then-withdraw pair never increases the caller's assets absent fees.

## 9. Regression test

```solidity
function testRoundTripDoesNotLeakAfterFix() public {
    vm.startPrank(attacker);
    for (uint256 i; i < 1_000; ++i) {
        uint256 s = pool.deposit(1 wei);
        pool.withdraw(s);
    }
    vm.stopPrank();
    assertGe(pool.totalLiquidity(), liqBefore - 1);  // ≤ 1 wei total drift
}
```

## 10. References

- Uniswap V2 core — `sqrt` rounding choices deliberately favor the pool.
- OpenZeppelin `Math.mulDiv` — full-precision multiplication and division.
- EIP-4626 Security Considerations — rounding direction and first-depositor interactions.
- Solmate / Solady ERC-4626 discussions on share-math rounding.
