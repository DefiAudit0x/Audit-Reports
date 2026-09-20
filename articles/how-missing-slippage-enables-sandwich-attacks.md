# How Missing Slippage Protection Turns an AMM Swap into a Sandwich Target

A swap can be mathematically correct and still give a user a surprisingly bad outcome.

One of the simplest examples is an AMM swap without slippage protection.

The problem is not necessarily a bug in the constant-product formula. The formula can behave exactly as designed. The problem is that the user may be allowing the transaction to execute at any price, as long as the transaction itself remains valid.

That creates an opportunity for another participant to manipulate the pool immediately before the swap and then trade back afterward.

This is the basic mechanism behind a **sandwich attack**.

I built a minimal AMM fixture to reproduce the behavior and make the effect measurable rather than treating MEV as an abstract concept.

## Start with a simple pool

Consider a constant-product pool containing:

- 100 units of token A
- 100 units of token B

The invariant is:

```text
x × y = k
```

So initially:

```text
100 × 100 = 10,000
```

Suppose a user wants to swap 10 A for B.

Ignoring fees for simplicity, the expected amount of B is approximately:

```text
100 - (10,000 / 110) ≈ 9.09 B
```

The user therefore has a reasonable expectation that the swap will return roughly 9 B.

But what happens if someone else gets their transaction in first?

## The sandwich

An attacker can construct two transactions around the victim's transaction:

```text
Attacker: front-run
Victim:   swap
Attacker: back-run
```

The attacker first buys B with A.

That changes the pool reserves and therefore changes the price available to the victim.

The victim's transaction is then executed against the manipulated reserves.

Finally, the attacker sells the B they acquired back into the pool.

The attacker has effectively used the victim's order as the middle part of a three-transaction strategy.

## A concrete example

In the test fixture, the difference becomes substantial.

Without the attacker, the victim's 10 A swap would receive approximately:

```text
9.07 B
```

After the attacker's front-run, the same victim transaction receives only:

```text
4.16 B
```

The transaction itself still succeeds.

There is no arithmetic failure.

The AMM is still applying its pricing formula.

The important difference is that the victim never specified how bad the execution price was allowed to become.

The attacker has moved the price immediately before the victim's transaction and then trades back afterward.

In the worked example, the attacker's round trip produces roughly:

```text
5.42 A
```

while the victim receives substantially less B than they would have received without the front-run.

The exact profitability of a real sandwich depends on factors such as pool fees, gas or priority costs, available liquidity, and transaction ordering. The important security property is not that every sandwich is profitable, but that the contract gives the user no execution-price boundary.

## The missing parameter is the important part

A typical swap interface can include something conceptually similar to:

```solidity
swap(
    amountIn,
    minAmountOut,
    recipient,
    deadline
)
```

The critical parameter here is:

```text
minAmountOut
```

It tells the contract:

> I am willing to accept this swap only if I receive at least this amount.

For example, if the user expects approximately 9.07 B, they might submit a transaction requiring at least 8.9 B.

Then the attacker's front-run cannot simply push the execution price down indefinitely.

The victim's transaction reaches the contract and the contract checks the actual output:

```solidity
require(amountOut >= minAmountOut);
```

If the price has moved too far, the transaction reverts instead of silently executing at an unacceptable price.

That changes the attacker's problem considerably.

They can still manipulate the pool, but they can no longer force the victim to accept arbitrary execution.

## Slippage protection is not the same as a deadline

There is another parameter that is easy to overlook:

```text
deadline
```

These two protections address different problems.

`minAmountOut` protects the **execution price**.

`deadline` protects against **stale transactions**.

A transaction can sit pending while market conditions change. Without a deadline, a transaction submitted under one set of assumptions may execute much later under a completely different price.

So a robust swap generally needs to consider both:

```text
minAmountOut → "How much am I willing to receive?"

deadline     → "How long is this transaction valid?"
```

They are complementary rather than interchangeable.

## Reproducing the attack with Foundry

I wanted the behavior to be reproducible rather than relying only on a conceptual explanation.

The fixture therefore contains:

1. A vulnerable AMM.
2. A normal victim swap.
3. An attacker front-run.
4. The victim swap against the manipulated reserves.
5. The attacker's back-run.
6. Assertions showing the difference in execution.
7. A corrected implementation.
8. Regression tests for the protection.

This makes the security property much easier to reason about.

Instead of saying:

> "This contract may be vulnerable to MEV."

we can test the actual property:

> A user's swap should not execute below the minimum output explicitly accepted by that user.

That is a much more useful property to carry into an audit.

## The fix

The simplest mitigation is to make the user's execution constraints explicit.

A protected swap should enforce both the minimum acceptable output and an expiration time:

```solidity
require(block.timestamp <= deadline);
require(amountOut >= minAmountOut);
```

The exact implementation depends on the AMM design, but the principle is straightforward:

**Do not make the user accept whatever price happens to exist when their transaction executes.**

Let the user define the boundary.

## Why this matters beyond one AMM

The interesting part of this issue is that nothing about the underlying pricing equation has to be broken.

The AMM can calculate prices correctly.

The contract can pass its internal accounting checks.

The transaction can execute successfully.

And the user can still receive a materially worse result than intended.

That distinction is important when reviewing DeFi systems.

Security is not only about preventing unauthorized state changes or stealing funds. It is also about checking whether the contract enforces the assumptions users are relying on.

For swaps, one of those assumptions is often:

> "I don't want this transaction to execute at an arbitrarily worse price."

If the contract does not encode that assumption through something like `minAmountOut`, the protocol may leave the user exposed to transaction-ordering strategies such as sandwiching.

## Takeaway

The vulnerable pattern is deceptively simple:

```text
User submits swap
        ↓
No minimum output
        ↓
Attacker moves pool price
        ↓
User executes at manipulated price
        ↓
Attacker trades back
```

The defensive pattern is equally simple:

```text
User specifies acceptable output
        ↓
Contract checks actual output
        ↓
Swap executes only within that boundary
```

The lesson is broader than sandwich attacks.

When auditing a DeFi protocol, it is worth asking not only whether the mathematical model is correct, but also whether the contract actually enforces the economic constraints that users expect.

A transaction succeeding is not the same thing as a transaction succeeding under acceptable conditions.

*This article is based on an educational AMM fixture and reproducible Foundry case study. It is not presented as a finding against a live production protocol.*
