# Case Study 002: `tx.origin` Authorization Bypass



**Classification:** Educational case study  

**Status:** Complete  

**Scope:** Authorization boundary in a withdrawal function  

**Repository:** [evm-audit-lab](https://github.com/DefiAudit0x/evm-audit-lab)



## Summary



The vulnerable example authorizes an emergency withdrawal with `tx.origin == owner`. This couples authorization to the outermost account in the call chain rather than to the contract that is directly invoking the function. A malicious intermediary contract can therefore trick the owner into calling it, then forward the call to the vault while preserving the owner as `tx.origin`.



This is an educational demonstration, not a finding against a production protocol and not a client audit.



## Threat model



The owner may interact with an untrusted contract, router, token, or phishing page. The attacker controls an intermediary contract and wants to make the vault interpret the owner as the authorized caller.



## Violated invariant



> Only the explicitly authorized contract caller, `msg.sender`, may invoke an owner-only administrative action.
> 


The vulnerable contract violates this invariant because it trusts `tx.origin`, which is not the immediate caller.



## Impact



If the owner is induced to call a malicious intermediary, the intermediary can invoke `emergencyWithdraw` and satisfy the `tx.origin == owner` check. The vault balance can then be redirected to an attacker-controlled recipient. The impact is **high in the intentionally vulnerable example**, but exploitability depends on the owner interacting with an untrusted call path.



## Reproduction outline



1. Deploy `VulnerableAccessControlVault` with funds.
2. 
2. Deploy an attacker-controlled intermediary contract.
3. 
3. Induce the owner to call the intermediary.
4. 
4. The intermediary calls `emergencyWithdraw`.
5. 
5. The vault sees the owner as `tx.origin` and transfers its balance.
6. 


A Foundry regression test should assert that the malicious intermediary succeeds against the vulnerable version and reverts against the fixed version.



## Remediation



Replace `tx.origin` authorization with `msg.sender == owner`. Validate the recipient, use a low-level call with an explicit success check, and consider a withdrawal process that separates authorization from fund movement when the asset or balance model is more complex.



## Verification checklist



| Check | Expected result |

|---|---|

| Direct owner call to the safe vault | Succeeds |

| Non-owner direct call | Reverts |

| Owner through malicious intermediary | Reverts in the safe vault |

| Zero-address recipient | Reverts |

| Transfer failure | Reverts and preserves state |



## Disclosure note



This case study is intentionally self-contained and educational. It contains no client information, private address, credential, or weaponized instruction for attacking a live system.







