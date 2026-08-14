# Educational Case Study 001: Reentrancy in a Vault Withdrawal Flow

**Classification:** Educational demonstration

**Severity:** High in the demonstrated threat model

**Status:** Complete

**Scope:** The intentionally vulnerable `VulnerableVault` example in the companion EVM Audit Lab repository.

## Executive summary

The vulnerable withdrawal flow sends Ether to the caller before reducing the caller's recorded balance. A malicious receiver can re-enter the vault during the external call and withdraw the same recorded balance more than once.

This is a deliberately minimal educational example. It is not a report on a production protocol and must not be presented as a client finding.

## Finding: state update occurs after an external call

The vulnerable function follows this order:

1. Read the caller's balance.
2. Send Ether to the caller.
3. Reduce the recorded balance.

The external call transfers control to untrusted code before the accounting invariant is restored. The attacker contract uses its fallback function to call `withdraw` again while the original balance is still non-zero.

## Impact

Under the demonstrated assumptions, an attacker can withdraw more Ether than their recorded balance, limited by the vault's available funds and the gas/execution environment. The issue violates the invariant:

> A successful withdrawal must reduce the user's claim before control is transferred to untrusted code.

## Reproduction

The companion test deposits funds for an attacker and a victim, executes the attack, and asserts that the attacker receives more than its recorded balance while the vault loses the victim's funds.

The test is intentionally self-contained and uses a minimal cheatcode interface rather than importing a third-party testing framework into the report repository.

## Remediation

The fixed implementation follows the checks-effects-interactions pattern: it validates the amount, decreases the user's balance, and only then performs the external transfer. A production implementation should also consider a reentrancy guard, pull-payment design, bounded gas behavior, and protocol-specific accounting invariants.

## Verification

The companion lab contains both the vulnerable and fixed implementations plus a regression test. The test should demonstrate the exploit against the vulnerable contract and confirm that the fixed contract rejects the reentrant second withdrawal.

## References

- [Solidity security considerations: re-entrancy](https://docs.soliditylang.org/en/latest/security-considerations.html#re-entrancy)
- [EVM Audit Lab](https://github.com/DefiAudit0x/evm-audit-lab)
