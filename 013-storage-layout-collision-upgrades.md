# Report 013: Storage Layout Collisions in Upgradeable Proxies

| Field | Value |
| --- | --- |
| **Type** | Educational case study |
| **Status** | Complete |
| **Date** | 2026-09-15 |
| **Language** | Solidity `^0.8.24` |
| **Severity** | Critical (see [severity matrix](./templates/severity-matrix.md)) |
| **Repository** | [evm-audit-lab — Lab 07](https://github.com/DefiAudit0x/evm-audit-lab) (runnable PoC) |

---

## 1. Summary

A hand-rolled proxy keeps its administration state — `admin` and `implementation` — in regular storage slots 0 and 1, the same slots the implementation contract uses for its own variables. Any state write the implementation performs through the proxy lands in the proxy's administration slots: in the lab, a single `setValue()` call through the proxy overwrites `admin` with an attacker-chosen value, and whoever owns `upgradeTo` owns every asset the proxy custodies. A sibling failure mode — inserting a variable mid-layout during an upgrade — silently rebinds every existing slot and freezes or corrupts user balances.

## 2. Background

The lab proxy (condensed from [Lab 07](https://github.com/DefiAudit0x/evm-audit-lab)):

```solidity
// VulnerableProxy.sol
address public admin;           // slot 0
address public implementation;  // slot 1

// VulnerableImplV1.sol
uint256 public value;           // slot 0 — SAME slot as proxy.admin
```

Delegatecall executes implementation code against proxy storage, so `value` and `admin` are the same 32 bytes. The proxy reserves none of the EIP-1967 keccak-derived slots that exist precisely to make this collision impossible.

## 3. Threat model

- **Asset at risk:** everything the proxy custodies — the end state is an upgrade to arbitrary logic.
- **Privileged actors:** the intended admin; the flaw is that adminship is writable by anyone who can reach an implementation state-write through the proxy.
- **Untrusted actors:** any user allowed to call the implementation's state-mutating functions — in the lab, `setValue` is permissionless.
- **Preconditions:** an implementation with a plain state variable in slot 0 (or any slot the proxy uses), reachable through the proxy.

## 4. Violated invariant

> Proxy administration state and implementation state must occupy disjoint storage slots.

With both rooted at slot 0, the sets intersect by construction, and the first delegated write to a colliding variable rewrites proxy administration.

## 5. Impact

Complete takeover in two transactions:

```text
1. attacker calls setValue(uint256(uint160(attacker))) through the proxy
   -> proxy storage slot 0 (admin) := attacker
2. attacker calls upgradeTo(evilImpl)
   -> arbitrary logic now executes in the proxy's context
   -> every asset the proxy holds is extractable
```

The upgrade-layout sibling has the same severity class with different symptoms: upgrading V1 to a V2 that *inserts* a variable before existing ones shifts every subsequent slot, so `balances` mappings read from empty slots — funds become invisible and permanently frozen, or worse, mis-accounted into theft if V2 re-registers them. Argued in both directions: a deployment whose implementation stores *no* plain variables in colliding slots cannot be hijacked this way — but nothing in the proxy enforces that property, and it silently breaks the day someone adds a field. **Critical**.

## 6. Technical details

Why the collision is silent: both layouts are individually valid. Solidity assigns proxies and implementations their storage independently, starting at slot 0; only the delegatecall composition overlaps them. Tests that exercise the implementation directly (not through the proxy) never observe the collision, and the proxy's own functions keep working until the exact slot a test writes is the one administration depends on.

The insertion variant, mechanically:

```text
V1 layout:  slot 0: owner          slot 1: balances (mapping root)
V2 (buggy): slot 0: owner  slot 1: feeBps (NEW)  slot 2: balances
             -> balances now reads V1's empty slot 2; every balance is zero
             -> withdrawals revert or funds strand, depending on V2's guards
```

## 7. Proof of Concept

Runnable in [Lab 07](https://github.com/DefiAudit0x/evm-audit-lab):

```bash
git clone https://github.com/DefiAudit0x/evm-audit-lab && cd evm-audit-lab
forge test --match-contract ProxyCollisionTest -vvv
```

Core assertion (condensed from `test/ProxyCollision.t.sol`):

```solidity
// Attacker sets a value that is also a valid address...
vm.prank(attacker);
VulnerableImplV1(address(proxy)).setValue(uint256(uint160(attacker)));

// ...and the proxy's admin silently becomes the attacker.
assertEq(proxy.admin(), attacker);

vm.prank(attacker);
proxy.upgradeTo(address(evilImpl));   // arbitrary logic upgrade — takeover complete
```

## 8. Remediation

1. Move proxy administration to the EIP-1967 keccak-derived slots (`keccak256("eip1967.proxy.implementation") - 1`, and the admin equivalent) — no sane compiler-assigned layout can reach them. This is exactly what the lab's `SafeProxy` does.
2. Treat upgrades as append-only: new variables go at the end of the layout, never inserted before existing ones; document the layout in the repository and verify it with an upgrade diff tool (e.g., `slither-check-upgradeability`) before every upgrade.
3. Add a proxy-level test that writes every implementation state variable through the proxy and asserts `admin()` / `implementation()` are unchanged — the regression that makes this class impossible to reintroduce silently.

## 9. Regression test

```solidity
function testSafeProxyAdminSurvivesImplementationWrites() public {
    address adminBefore = safeProxy.admin();
    vm.prank(user);
    SafeImplV1(address(safeProxy)).setValue(type(uint256).max);
    SafeImplV2(address(safeProxy)).setExtra(7);
    assertEq(safeProxy.admin(), adminBefore);       // administration untouched
}
```

## 10. References

- EIP-1967 — Proxy Storage Slots (the keccak-derived slot convention).
- OpenZeppelin — Transparent vs UUPS proxy patterns and storage-collision guidance.
- Parity Multisig incident post-mortem (November 2017) — storage-collision family.
- Trail of Bits, "How to Prevent Storage Collisions in Solidity".
