# Case Study 003: Stale Oracle Data



**Classification:** Educational case study  

**Status:** Complete  

**Scope:** Price freshness and round-completeness checks  

**Repository:** [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab)



## Summary



The vulnerable consumer accepts a positive oracle answer without checking whether the answer is fresh or whether the reported round is complete. During an outage, delayed update, sequencer problem, or market dislocation, a protocol can continue valuing collateral or debt with a materially outdated price.



This is an educational model. It is not a statement that any named oracle or production protocol is vulnerable.



## Threat model



The oracle may temporarily stop updating, return a delayed round, or expose an answer whose timestamp is outside the protocol's risk window. An attacker seeks to borrow against overvalued collateral or liquidate positions using an obsolete price.



## Violated invariant



> A price used for risk-sensitive accounting must be positive, complete, and newer than the protocol's maximum acceptable age.
> 


The vulnerable consumer checks only that the answer is positive.



## Impact



The impact depends on the protocol's accounting model and market volatility. A stale price can cause under-collateralized borrowing, incorrect liquidation, bad share pricing, or mispriced swaps. Severity should be determined from the actual protocol flow, oracle fallback behavior, and the maximum stale window—not from the presence of a missing check alone.



## Reproduction outline



1. Deploy a mock feed with a valid positive answer and an old `updatedAt`.
2. 
2. Call `collateralValue` on the vulnerable consumer; it accepts the stale price.
3. 
3. Call the safe consumer with the same feed and a bounded `maxAge`.
4. 
4. Confirm that the safe consumer reverts with `stale price`.
5. 
5. Repeat with `answeredInRound < roundId` and confirm the incomplete round guard.
6. 


## Remediation



Validate that the answer is positive, `updatedAt` is nonzero, the age is within the configured risk window, and the answer belongs to a complete round. Choose `maxAge` from protocol risk analysis, document the fallback behavior, and test boundary values around the freshness threshold.



## Verification checklist



| Check | Expected result |

|---|---|

| Fresh positive answer | Accepted |

| Zero or negative answer | Rejected |

| `updatedAt == 0` | Rejected |

| Price older than `maxAge` | Rejected |

| Incomplete round | Rejected |

| Timestamp exactly at the policy boundary | Covered by an explicit boundary test |



## Disclosure note



This report is an independent educational case study. It does not describe a client engagement and should not be used as evidence that a live protocol is insecure without a separate authorized review.







