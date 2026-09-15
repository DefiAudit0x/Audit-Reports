# Report 011: Unbounded Loop Denial of Service

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

A revenue splitter distributes to a payee list that anyone can append to, with no cap. Each payee costs a fixed amount of gas to pay, so once the list grows past the block gas limit divided by that per-payee cost, `distribute()` can no longer complete for anyone — it reverts, permanently, for every caller. Funds remain in the contract with no alternative exit path. Educational case study on a fixture splitter.

## 2. Background

The vulnerable contract:

```solidity
// Splitter.sol, L30-L42
address[] public payees;                        // global, unbounded

function addPayee(address p) external {         // permissionless — anyone may append
    payees.push(p);
}

function distribute() external {
    uint256 n = payees.length;                  // cost scales with global state
    for (uint256 i = 0; i < n; ++i) {
        _pay(payees[i], owed[payees[i]]);       // ~25k gas per payee
    }
}
```

Nothing bounds `payees.length`, and nothing lets an individual payee extract their share outside the shared loop.

## 3. Threat model

- **Asset at risk:** the contract's entire revenue balance — frozen, not stolen (absent a secondary flaw).
- **Privileged actors:** none — `addPayee` is open, `distribute` is open.
- **Untrusted actors:** any address; the attack is registering many payees, each a fresh contract to also make `_pay` slightly more expensive via expensive receive logic.
- **Preconditions:** gas per payee times list length exceeds the block gas limit — roughly a few thousand payees at 30M gas, cheaper to arrange than it sounds.

## 4. Violated invariant

> The gas cost of a user-triggered operation must not scale with state that untrusted parties can grow without bound.

`distribute()` is O(global payee count), and the count is attacker-controlled. Once the product crosses the block gas limit, the operation is not slow — it is impossible.

## 5. Impact

Total and permanent loss of availability: `distribute()` reverts out-of-gas for every caller, no payee can be paid individually, and the balance sits frozen. The attacker gains nothing directly — this is pure griefing — which bounds the practical severity at DoS rather than theft.

Argued in both directions: if the contract had an owner-operated `removePayee`, an emergency `sweep`, or a per-payee `claim()` fallback, the freeze would be recoverable and severity would drop to Low (temporary disruption). The fixture has none, so Medium: lasting denial of access to real funds, with no direct loss of custody beyond that denial.

## 6. Technical details

The economics of the freeze, with round numbers:

```text
per-payee cost:  ~25,000 gas (transfer + storage reads + cold account)
block gas limit: 30,000,000
freeze point:    30,000,000 / 25,000 ≈ 1,200 payees

attacker cost:   1,200 × (20,000 gas push + 21,000 gas deploy)
                 ≈ 49M gas ≈ a few dollars at typical base fees
```

Because `addPayee` is a plain push, the attacker does not even need contracts — 1,200 distinct EOAs or a single contract calling `addPayee` 1,200 times from a loop both work. Once the threshold is crossed, the very transaction that crosses it (or the first `distribute()` after) reverts: the contract is bricked with no code path to recover.

## 7. Proof of Concept

```solidity
// test/SplitterDos.t.sol (educational sketch)
function testDistributeBricksPastGasLimit() public {
    for (uint256 i; i < 1_500; ++i) {           // ~1,500 payees exceeds 30M gas
        splitter.addPayee(address(uint160(i + 1)));
    }

    vm.expectRevert();                          // out of gas
    splitter.distribute{gas: 30_000_000}();

    // and there is no alternative exit:
    // splitter has no claim(), no sweep(), no removePayee()
}
```

Run with:

```bash
forge test --match-test testDistributeBricksPastGasLimit -vv
```

## 8. Remediation

Any one of the following restores availability; the first is preferred:

1. **Chunked distribution with a cursor** — process at most `K` payees per call, persist `uint256 cursor`, and let repeated calls walk the list. Per-call cost is constant and user-bounded.
   ```solidity
   function distribute(uint256 maxPayees) external {
       uint256 end = cursor + maxPayees;
       if (end > payees.length) end = payees.length;
       for (uint256 i = cursor; i < end; ++i) _pay(payees[i], owed[payees[i]]);
       cursor = end == payees.length ? 0 : end;
   }
   ```
2. **Pull payments** — each payee calls `claim()` for themselves; cost scales with one's own claim, never with global state.
3. **Cap the list** — `require(payees.length < MAX_PAYEES, "full")` at `addPayee`, keeping a single-transaction `distribute()` within the block gas limit by construction.

## 9. Regression test

```solidity
function testChunkedDistributeAlwaysCompletes() public {
    for (uint256 i; i < 1_500; ++i) splitter.addPayee(address(uint160(i + 1)));

    while (!splitter.cycleComplete()) {
        splitter.distribute(100);               // bounded gas per call — never reverts
    }
    assertTrue(splitter.cycleComplete());       // everyone eventually paid
}
```

## 10. References

- SWC-128 — Denial of Service.
- OpenZeppelin `PullPayment` — the pull-over-push payment pattern.
- ConsenSys Smart Contract Best Practices — "bounded loops and gas-limit DoS".
- Ethereum.org — gas limits and block-level execution constraints.
