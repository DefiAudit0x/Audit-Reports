# Report 010: Uninitialized UUPS Proxy Takeover

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

A UUPS-upgradeable vault ships an `initialize()` without the `initializer` modifier, and the implementation's constructor never calls `_disableInitializers()`. The proxy is deployed in one transaction and initialized in a later one. In the window between — or forever, if the initializer is simply never invoked — the first arbitrary caller becomes the owner: they can re-initialize, then `upgradeToAndCall` a malicious implementation and drain every asset the proxy holds. Independent research on an educational fixture.

## 2. Background

The implementation contract:

```solidity
// Vault.sol (implementation)
contract Vault is Initializable, UUPSUpgradeable, OwnableUpgradeable {
    function initialize(address owner_) public {          // ← missing `initializer` modifier
        __Ownable_init(owner_);
    }

    function _authorizeUpgrade(address) internal override onlyOwner {}   // owner-gated, but owner is unset
    // no constructor calling _disableInitializers() on the implementation itself
}
```

The deployment script creates the proxy and intends to initialize it in a follow-up transaction — a two-step deployment that leaves the vault in its most dangerous state.

## 3. Threat model

- **Asset at risk:** every asset the proxy custodies — the takeover ends in an arbitrary-logic upgrade, so the ceiling is the full balance.
- **Privileged actors:** nobody yet — that is the bug: the owner is `address(0)` until `initialize` runs, and nothing restricts who may run it.
- **Untrusted actors:** anyone watching the mempool for the proxy-creation transaction, or anyone scanning chain state for uninitialized proxies.
- **Preconditions:** a deployed-but-uninitialized proxy, or one whose initialization is frontrunnable. Both are code properties, not deployment accidents the code prevents.

## 4. Violated invariant

> Privileged protocol state must be established exactly once, atomically with deployment, by the deployer.

Because `initialize` is unguarded, privileged state can instead be established by whoever moves first — and the code does not even guarantee "once": the same function can be re-run on an already-owned proxy to steal ownership back.

## 5. Impact

Full loss of custody, in three transactions:

```text
1. attacker.initialize(attacker)                 — proxy storage: owner = attacker
2. attacker.upgradeToAndCall(evilImpl, drain())  — logic swapped, arbitrary code executes
3. evilImpl drains every token and wei held by the proxy
```

There is a second, independent consequence of the same defect: the *implementation* contract itself can be initialized by anyone. Owning the implementation does not directly own the proxy (delegatecall runs implementation code against proxy storage), but an attacker-owned implementation can be self-destructed, bricking every proxy that points at it — a permanent-denial-of-service variant with no fund recovery, the Parity freeze pattern.

Argued in both directions: if the deployment script had initialized the proxy inside the same transaction as proxy creation, the takeover window would never open — but nothing in the code enforces that ordering, and the uninitialized implementation remains attacker-initializable forever. Audit practice rates the unguarded initializer Critical because the exploit requires no special access and its success probability only depends on deployment hygiene. **Critical**.

## 6. Technical details

Why the window exists:

- `initialize()` without the `initializer` modifier has no one-shot guard — any caller, any number of times.
- The implementation constructor does not call `_disableInitializers()`, so the implementation's *own* storage can be initialized by anyone (it usually holds no funds, but its logic can be hijacked or destroyed).
- The proxy was created in transaction N and initialized in transaction N+1; between them the contract exists with `owner == address(0)` and a callable `initialize`.

Frontrunning completes the attack even when the deployer intends to initialize promptly: the initialization transaction sits in the mempool, and the attacker's identical transaction with a higher tip lands first.

## 7. Proof of Concept

```solidity
// test/UupsTakeover.t.sol (educational sketch)
function testUninitializedProxyIsTakenOver() public {
    address proxy = _deployVaultProxy();              // deployed, not yet initialized

    vm.prank(attacker);
    Vault(proxy).initialize(attacker);                // attacker becomes owner

    vm.prank(attacker);
    Vault(proxy).upgradeToAndCall(
        address(evilImpl),
        abi.encodeWithSelector(Evil.drain.selector)
    );

    assertEq(token.balanceOf(attacker), TOTAL_DEPOSITS);   // vault emptied
}

function testImplementationCanBeReinitialized() public {
    vm.prank(attacker);
    Vault(implementation).initialize(attacker);       // implementation storage hijacked
}
```

Run with:

```bash
forge test --match-test testUninitializedProxy -vv
```

## 8. Remediation

Three layers, all of them standard:

```diff
  function initialize(address owner_) public initializer {   // ← one-shot guard
      __Ownable_init(owner_);
  }

+ constructor() {
+     _disableInitializers();       // implementation can never be initialized
+ }
```

Additionally: initialize the proxy **in the same transaction** that creates it (ERC1967Proxy constructor argument), place `upgradeTo` behind a timelock so any future ownership accident is reviewable, and add a deployment test asserting `owner() != address(0)` immediately after the proxy creation transaction.

## 9. Regression test

```solidity
function testTakeoverFailsAfterFix() public {
    address proxy = _deployAndInitializeVault();      // atomic deploy + initialize

    vm.prank(attacker);
    vm.expectRevert();                                // Initializable: already initialized
    Vault(proxy).initialize(attacker);

    vm.prank(attacker);
    vm.expectRevert();                                // implementation locked too
    Vault(implementation).initialize(attacker);
}
```

## 10. References

- OpenZeppelin Upgradeable Contracts — `initializer`, `reinitializer`, and `_disableInitializers` guidance.
- Parity Multisig post-mortem (November 2017) — uninitialized library wallet; 513k ETH frozen.
- Trail of Bits, "Building Secure Contracts" — upgradeable contract initialization checklist.
- ERC-1967 — proxy storage slots and deployment patterns.
