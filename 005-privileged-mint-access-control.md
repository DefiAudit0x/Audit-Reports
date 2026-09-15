# Report 005: Privileged Mint via Access-Control Flaw

| Field | Value |
| --- | --- |
| **Type** | Independent research |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Critical (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | Educational fixture, pattern from [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab) |

---

## 1. Summary

A bridge-minted collateral token exposes two minting entry points: a role-gated `mintTo()` used by the bridge, and an older `mint()` left over from a pre-audit revision that lacks the `onlyRole(MINTER_ROLE)` modifier. Anyone can call the unprotected function and mint arbitrary supply, breaking the token's backing and collapsing the value held by every holder. Independent research on an educational fixture; no live protocol is implicated.

## 2. Background

The fixture is a bridge collateral token built on OpenZeppelin `AccessControl`:

```solidity
// BridgeToken.sol, L28-L36
bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

function mintTo(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
    _mint(to, amount);                    // gated — used by the bridge
}

function mint(address to, uint256 amount) external {
    _mint(to, amount);                    // legacy duplicate — no modifier
}
```

`mint()` is a leftover from before the role model was introduced, and it was never removed or gated when `mintTo()` landed.

## 3. Threat model

- **Asset at risk:** the entire circulating value of the token — backing per unit collapses as supply grows.
- **Privileged actors:** `MINTER_ROLE` holders (intended: the bridge validator set); `DEFAULT_ADMIN_ROLE` (role grantor).
- **Untrusted actors:** any address — the vulnerable entry point is permissionless.
- **Preconditions:** none beyond the flawed deployment; the attack succeeds in a single transaction with no capital requirement.

## 4. Violated invariant

> Total supply may only grow through the role-gated bridge path.

`mint()` lets an unprivileged caller grow supply outside that path, so the invariant fails at the first call.

## 5. Impact

Unbounded minting is a direct value-capture primitive: the attacker mints and sells into whatever liquidity backs the token — DEX pools, lending markets, the bridge's redemption reserve — extracting value up to those reserves before the market reprices. Holders and the backing pool absorb the loss, and the token's peg typically does not recover.

Argued in both directions: nothing lowers this rating — the fixture has no pause, mint cap, or timelock that would bound the damage; and Critical is the ceiling of the severity matrix, so no higher rating exists. **Critical**.

## 6. Technical details

Execution path:

```text
attacker -> BridgeToken.mint(attacker, 1_000_000e18)    // no role check
          -> sells into the backing pool / lending market
          -> value extracted; supply permanently inflated
```

The flaw class is **protected function duplicated unprotected**: a gated function and an ungated one that perform the same privileged operation. Such duplicates survive refactors because tests exercise only the new entry point, and role reviews focus on where roles are checked rather than where they are missing. Diff-based review of every external function that mutates privileged state is the reliable countermeasure.

## 7. Proof of Concept

```solidity
// test/MintAccessControl.t.sol (educational sketch)
function testAnyoneCanMint() public {
    vm.startPrank(attacker);             // attacker holds no roles whatsoever
    uint256 before = token.totalSupply();
    token.mint(attacker, 1_000_000e18);  // succeeds — must revert
    assertGt(token.totalSupply(), before);
    vm.stopPrank();
}
```

Run with:

```bash
forge test --match-test testAnyoneCanMint -vv
```

## 8. Remediation

Delete the legacy entry point, or gate it identically:

```diff
- function mint(address to, uint256 amount) external {
-     _mint(to, amount);
- }
+ // removed: legacy duplicate of mintTo()
```

If the function must remain for interface compatibility, apply `onlyRole(MINTER_ROLE)`. Beyond the diff: add a test asserting that every external function performing a privileged operation reverts for a role-less caller, verify on deployment that no role was granted incidentally, and place admin keys behind a timelock so a future grant mistake is reviewable.

## 9. Regression test

```solidity
function testMintRevertsForRolelessCaller() public {
    vm.prank(attacker);
    vm.expectRevert();
    token.mint(attacker, 1);
}
```

## 10. References

- OpenZeppelin — `AccessControl` documentation and role-management checklists.
- Wormhole incident (February 2022) — mint path reached without a valid guardian signature.
- Poly Network incident (August 2021) — privileged cross-chain keeper roles rewritten.
- Smart Contract Weakness Classification — SWC-105: Access Control.
