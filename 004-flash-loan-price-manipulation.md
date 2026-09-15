# Report 004: Flash Loan Price Manipulation via Spot-Price Oracle

| Field | Value |
| --- | --- |
| **Type** | Independent research |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | High (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | Educational fixture, pattern from [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) |

---

## 1. Summary

A money market reads its collateral price directly from a DEX pair's spot reserve ratio. Because that ratio can be skewed by a single swap and restored in the same transaction, an attacker with flash-loan access can inflate the marked price of the collateral, borrow against the overvalued position, and leave the lending pool under-collateralized. This report walks through the mechanics as independent research on an educational fixture; it is not a claim about any live protocol.

## 2. Background

The fixture models a minimal lending market (`LendingMarket`) that accepts one collateral token and lends one stable asset. Pricing is delegated to an `IOracle` implementation that reads a Uniswap-V2-style pair:

```solidity
// oracle/SpotOracle.sol, L18-L22
function price(address token) external view returns (uint256) {
    (uint256 rA, uint256 rB,) = IPair(pairFor(token)).getReserves();
    return (rB * 1e18) / rA; // quote per collateral — spot, unbounded
}
```

The market applies a loan-to-value ratio to that price when minting debt. Nothing between the pair read and the borrow path bounds how far the observable price can move, or how quickly it must revert.

## 3. Threat model

- **Asset at risk:** lender-side funds in the stable-asset pool (protocol insolvency, not a direct transfer).
- **Privileged actors:** none required for the attack; the path is fully permissionless.
- **Untrusted actors:** any user with access to flash-loan liquidity comparable to the pair's reserves.
- **Preconditions:** the pair holds enough borrow-side depth; the market has no staleness or deviation guard; both legs fit in one atomic transaction.

## 4. Violated invariant

> The price used for collateral accounting must not be movable by a single atomic transaction.

Spot reserve ratios violate this by construction: a swap changes the observable price immediately, and the attacker can undo the change before the transaction ends, so the protocol never observes the restored ratio.

## 5. Impact

The attacker borrows `LTV × inflatedValue` while posting collateral worth roughly `realValue`. The pool's loss is the difference between the debt minted and the collateral's fair value at liquidation, minus flash-loan premiums and swap fees. In a shallow pair — a common configuration for long-tail collateral — a modest flash loan moves the spot price by an order of magnitude, so a 75%-LTV market can lose most of its lending depth in one transaction.

Honest bounds, argued in both directions: in deep pools with conservative LTVs, slippage and capital requirements can make the attack unprofitable — but that is an economic mitigation, not a structural one. The invariant remains violated, and the same setup becomes profitable again whenever pool depth falls or LTV parameters are raised. Severity in this fixture: **High**.

## 6. Technical details

Attack path inside a single transaction:

```solidity
// 1. Flash-borrow the stable asset.
// 2. Swap a large amount into the collateral pair — spot price of COLLATERAL rises.
// 3. Call LendingMarket.deposit(collateral) + borrow():
//      borrowable = collateralAmount * inflatedPrice * LTV / 1e18
// 4. Swap the collateral back through the pair, restoring reserves.
// 5. Repay the flash loan plus premium; keep the borrow proceeds minus fees
//    and the collateral now owed by the attacker's position.
```

The vulnerable dependency is the oracle call shown in section 2; the market itself performs no secondary or sanity check on the price it receives.

## 7. Proof of Concept

```solidity
// test/SpotManipulation.t.sol (educational sketch)
function testSpotPriceInflatesBorrow() public {
    uint256 flash = 2_000_000e18; // stable asset
    vm.startPrank(attacker);
    flashLender.flashLoan(attacker, stable, flash, "");
    // inside the callback:
    //   swap 1.9M stable -> collateral through the pair   (spot price x ~20)
    //   market.deposit(collateralReceived)
    //   market.borrow(market.maxBorrow(attacker))          // priced at skewed ratio
    //   swap collateral back to restore reserves
    //   repay flash loan + 0.09% premium

    uint256 debtMinted = market.debtOf(attacker);
    uint256 fairValue  = collateral * fairPrice / 1e18;
    assertGt(debtMinted, fairValue * 3 / 2); // borrowed well above fair value
    vm.stopPrank();
}
```

Run with:

```bash
forge test --match-test testSpotPriceInflatesBorrow -vv
```

## 8. Remediation

Replace the spot read with a manipulation-resistant source, and bound how much any single observation can matter:

1. Use a time-weighted average price over a window sized to the protocol's risk appetite, with a freshness check — a single-block skew then barely moves the average.
2. Cross-check a secondary source (e.g., aggregated feeds) and reject borrows when the two disagree beyond a configured threshold.
3. Cap LTV for collateral whose liquidity depth is shallow relative to the lending pool.

The narrowest correct fix for the fixture is the TWAP read plus a maximum-staleness guard, mirroring the freshness policy in [003 — Stale Oracle Data](./003-stale-oracle.md).

## 9. Regression test

```solidity
function testSpotManipulationFailsWithTwap() public {
    // Same attack script, oracle swapped for a 30-minute TWAP.
    // Assert: borrow reverts via the deviation guard,
    // or borrowable <= fairValue * LTV (skew contributes ~zero).
}
```

## 10. References

- bZx incidents (February and September 2020) — early flash-loan-assisted oracle manipulations.
- Mango Markets manipulation (October 2022) — oracle inflation without a flash loan.
- Uniswap V2 documentation — TWAP oracles and the cost of manipulation.
- Chainlink — Data Feeds guidance on staleness and heartbeat parameters.
