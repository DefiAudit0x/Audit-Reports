# Report 009: EIP-712 Signature Replay Across Chains and Nonces

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

An off-chain-signed voucher can be redeemed on-chain for value. The EIP-712 digest binds the voucher to its issuer and to the contract address, but the struct carries no nonce and the domain separator omits the chain ID. The same signature therefore spends twice on the same chain, and again on every chain — L2, fork, or re-deployment — where the contract exists at the same address. Independent research on an educational fixture; no live protocol is implicated.

## 2. Background

The fixture redeems signed vouchers:

```solidity
// VoucherPool.sol, L26-L41
struct Voucher { address to; uint256 amount; uint64 deadline; }

bytes32 private constant DOMAIN = keccak256(
    abi.encode(
        keccak256("VoucherPool"),
        keccak256("1"),
        address(this)
    )                                        // ← chainId missing from the domain
);

function redeem(Voucher calldata v, bytes calldata sig) external {
    require(block.timestamp <= v.deadline, "expired");

    bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN, hashVoucher(v)));
    require(ECDSA.recover(digest, sig) == issuer, "bad signature");

    // ← no nonce in the struct, no spent-signature record

    payable(v.to).transfer(v.amount);
}
```

Signature validity is checked correctly — uniqueness and chain-binding are not.

## 3. Threat model

- **Asset at risk:** the issuer's entire funded balance — every voucher is redeemable repeatedly until the pool drains.
- **Privileged actors:** the issuer (the only legitimate signer).
- **Untrusted actors:** any recipient of a valid voucher, and any observer of a redeemed voucher in a public mempool or event log (a redeem is itself proof the signature was once valid).
- **Preconditions:** the attacker obtains any one valid signature — legitimately issued, frontrun from the mempool, or scraped from an explorer after a first honest redemption.

## 4. Violated invariant

> A signature authorizes exactly one state transition, on exactly one chain, at most once.

With no nonce consumed and no chain ID in the domain, the signature authorizes the same transition an unbounded number of times on an unbounded number of chains.

## 5. Impact

Same-chain replay doubles every payment: redeem, then redeem again — the digest is identical, the signature is still valid, nothing marks it spent. Cross-chain replay is broader still: contracts deployed deterministically (CREATE2, or the same deployer nonce + bytecode) share an address across chains and forks; a domain separator built without `chainId` validates identically on each, so one signature drains every copy. Because vouchers are transferable by design (`v.to` need not be the redeemer), a redeemed voucher appearing in an explorer is a reusable proof-of-payment.

Argued in both directions: restricting the issuer to a single-chain deployment with private, one-time vouchers would confine the impact to the same-chain double spend — still unbounded value loss. Nothing in the contract enforces any of those restrictions. Severity: **High**.

## 6. Technical details

Both replay vectors:

```text
Vector A — same chain:
  1. issuer signs Voucher{to: A, amount: 10e18, deadline: T}
  2. A redeems; pool pays 10e18. No state records the spend.
  3. A redeems the identical calldata again; digest and signature still verify. Pool pays again.

Vector B — cross chain:
  1. the same bytecode is deployed at address 0xC on chains 1 and 2
  2. DOMAIN is identical on both (no chainId term), so a digest signed for 0xC on chain 1
     verifies on 0xC on chain 2
  3. a voucher issued for the chain-1 pool drains the chain-2 pool as well
```

## 7. Proof of Concept

```solidity
// test/VoucherReplay.t.sol (educational sketch)
function testVoucherReplaysOnSameChain() public {
    (Voucher memory v, bytes memory sig) = _signVoucher(attacker, 10 ether);

    pool.redeem(v, sig);                    // first redemption pays
    pool.redeem(v, sig);                    // must revert — pays again instead

    assertEq(attacker.balance, 20 ether);   // 2x the signed amount
}

function testVoucherReplaysAcrossChains() public {
    (Voucher memory v, bytes memory sig) = _signVoucher(attacker, 10 ether);

    vm.chainId(1);
    poolOnChain1.redeem(v, sig);

    vm.chainId(2);                          // same bytecode, same address
    poolOnChain2.redeem(v, sig);            // must revert — same signature accepted
}
```

Run with:

```bash
forge test --match-test testVoucherReplays -vv
```

## 8. Remediation

Bind the signature to one spend and one chain:

```diff
  struct Voucher {
      address to;
      uint256 amount;
      uint64 deadline;
+     uint256 nonce;                        // per-issuer, unique per voucher
  }

+ uint256 public constant CHAIN_ID = block.chainid;   // or cache at deploy and re-check
  bytes32 private constant DOMAIN = keccak256(
      abi.encode(
          keccak256("VoucherPool"),
          keccak256("1"),
-         address(this)
+         block.chainid,
+         address(this)
      )
  );

  function redeem(Voucher calldata v, bytes calldata sig) external {
      require(block.timestamp <= v.deadline, "expired");
+     bytes32 vhash = hashVoucher(v);
+     require(!spent[vhash], "already redeemed");
+     spent[vhash] = true;
      // ...
  }
```

Prefer an OpenZeppelin-style `nonces[issuer]` counter included in the struct over a `spent` map of digests: it is cheaper, gives the issuer ordered cancellation, and matches the EIP-2612 `permit` design everyone already knows how to sign correctly.

## 9. Regression test

```solidity
function testSecondRedeemRevertsAfterFix() public {
    (Voucher memory v, bytes memory sig) = _signVoucher(attacker, 10 ether);

    pool.redeem(v, sig);

    vm.expectRevert("already redeemed");
    pool.redeem(v, sig);                    // replay is now impossible
}
```

## 10. References

- EIP-712 — typed structured data hashing; domain separator composition.
- EIP-2612 — `permit` extension; the canonical nonce-based replay protection design.
- SWC-121 — Missing Protection Against Signature Replay Attacks.
- OpenZeppelin `ECDSA`, `Nonces`, and `MessageHashUtils` documentation.
