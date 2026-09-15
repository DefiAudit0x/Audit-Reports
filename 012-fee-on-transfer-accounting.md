# Report 012: Fee-on-Transfer Token Accounting Break

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

A simple vault credits depositors with the *requested* deposit amount while the vault's token balance grows by the *received* amount — and for fee-on-transfer tokens those differ. Each deposit through such a token mints claims exceeding real backing by the fee fraction; the shortfall accrues to the pool and is silently socialized onto honest depositors. An attacker can cycle deposits through the fee token deliberately, extracting the accumulated deficit. Educational case study on a fixture vault.

## 2. Background

The deposit path:

```solidity
// SimpleVault.sol, L22-L28
function deposit(uint256 amount) external returns (uint256 shares) {
    token.transferFrom(msg.sender, address(this), amount);   // may deliver < amount
    shares = amount;                                          // ← credits the requested amount
    balances[msg.sender] += shares;                           // claims exceed received value
}

function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount, "insufficient");
    balances[msg.sender] -= amount;
    token.transfer(msg.sender, amount);                        // pays out full claims
}
```

With a 10% fee token, a 100-token deposit transfers in 90 tokens and credits a 100-token claim — ten tokens of phantom value created out of the shared pool.

## 3. Threat model

- **Asset at risk:** the vault's real backing — the deficit is borne pro-rata by every honest depositor.
- **Privileged actors:** none required; if the vault whitelists tokens, the flaw activates the moment a fee token (or a fee-wrapping router) is allowed.
- **Untrusted actors:** any depositor able to interact through a fee-on-transfer token — including one they deployed themselves for the purpose.
- **Preconditions:** deposits of a token that delivers less than instructed; fee-on-transfer and some rebasing tokens behave this way.

## 4. Violated invariant

> Credited claims must equal value actually received by the vault.

Crediting `amount` while receiving `amount − fee` violates the invariant on every deposit, and the gap never closes — withdrawals pay full claims against short backing.

## 5. Impact

Per cycle, the attacker's extraction equals the fee fraction of their deposit: deposit 100, receive credit 100, withdraw 100 while the vault only ever held 90 — the missing 10 comes from everyone else's backing. Repeated and scaled, the drain approaches the vault's honest deposits. For an accidentally-listed fee token with organic volume, the same arithmetic acts as a slow insolvency mechanism: solvency erodes on every deposit until the first large honest withdrawal fails.

Argued in both directions: if the vault only ever supports standard ERC-20s that deliver the full amount (or `amount == 0` edge behavior is well-defined), the code path is dormant — but nothing in the contract enforces the token list, and "compatible with any ERC-20" is exactly the assumption this defect smuggles in. Severity for the fixture: **Medium** — an integration flaw with direct, quantifiable loss of backing.

## 6. Technical details

Balance trace of one attack cycle (10% fee token):

```text
start:  vault real balance = 100 (from honest depositors)

1. attacker.deposit(100)        fee token delivers 90
        vault real balance = 190
        attacker credit         = 100        ← phantom +10

2. attacker.withdraw(100)       vault pays out 100
        vault real balance = 90
        honest depositors' claims = 100      ← 10 claims now unbacked

repeat: each cycle moves another 10 tokens from honest backing to the attacker
```

The root cause is trusting the *instruction* (`amount`) over the *observation* (balance delta). The same class covers rebasing tokens that shrink balances between deposit and accounting, and tokens returning `false` instead of reverting on failure (see [008 — Unchecked Call Return Value](./008-unchecked-call-return-value.md) for that sibling).

## 7. Proof of Concept

```solidity
// test/FeeOnTransferVault.t.sol (educational sketch)
contract FeeToken is ERC20 {                       // 10% fee on every transfer
    function _update(address, address, uint256 amount) internal override {
        super._update(from, to, amount - (amount / 10));
    }
}

function testDepositThroughFeeTokenDrainsBacking() public {
    FeeToken ft = new FeeToken();
    vm.startPrank(attacker);
    ft.approve(address(vault), 100e18);
    vault.deposit(100e18);                          // credited 100e18, received 90e18
    vault.withdraw(100e18);                         // paid 100e18
    vm.stopPrank();

    assertEq(vault.realBacking(), 90e18);           // honest pool short 10e18
    assertGt(vault.totalClaims(), vault.realBacking());
}
```

Run with:

```bash
forge test --match-test testDepositThroughFeeTokenDrainsBacking -vv
```

## 8. Remediation

Credit what actually arrived, using the balance-delta pattern:

```diff
  function deposit(uint256 amount) external returns (uint256 shares) {
+     uint256 balBefore = token.balanceOf(address(this));
      token.transferFrom(msg.sender, address(this), amount);
+     uint256 received = token.balanceOf(address(this)) - balBefore;
+     require(received > 0, "nothing received");
-     shares = amount;
+     shares = received;
      balances[msg.sender] += shares;
  }
```

Prefer `SafeERC20.safeTransferFrom` for revert-on-failure semantics, document the vault's token policy explicitly (standard tokens only, or fee-on-transfer supported via deltas), and for rebasing tokens add a sync/snapshot strategy so shrinkage is absorbed by the share-price mechanism rather than by solvency.

## 9. Regression test

```solidity
function testFeeTokenDepositCreditedAtReceived() public {
    vm.startPrank(attacker);
    ft.approve(address(vault), 100e18);
    vault.deposit(100e18);
    vm.stopPrank();

    assertEq(vault.balanceOf(attacker), 90e18);     // credited what arrived
    assertEq(vault.realBacking(), vault.totalClaims()); // solvent
}
```

## 10. References

- OpenZeppelin `SafeERC20` documentation — non-standard token notes (fee-on-transfer, rebasing).
- Uniswap V2 core — the canonical balance-delta pattern for token deposits.
- ERC-20 specification — why transfer semantics are weaker than they look.
- ConsenSys Smart Contract Best Practices — accounting for non-standard ERC-20 behavior.
