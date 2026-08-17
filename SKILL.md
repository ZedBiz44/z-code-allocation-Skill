---
name: z-code-allocation
description: Look up, reserve, confirm, fail, or check authoritative record codes through the configured central allocator.
---

# Code Allocation

Use the configured central allocator whenever a governed knowledge record requires an authoritative code. Never calculate, guess, increment, copy, or reuse a code manually.

## Workflow

- Determine the proposed name key, owning collection, lane or category, and record type.
- Look up likely existing identities before reserving a new code.
- Allocate before creating the final record and retain the stable request identifier.
- If allocation requires review, stop that record and report the review identifier.
- Create the record with the returned code exactly as issued.
- Verify the stored record and its final type before confirming the allocation.
- If record creation fails, mark the allocation failed with the reason. Never recycle it.

## Runtime Profile

Use the allocator command, endpoint, credentials, classifications, and review owner supplied by the active implementation profile. Never print or store allocator credentials in pages, logs, prompts, or repositories.

## Governance and Operational Records

The authoritative technical copy and current deployment evidence are maintained in the [ZedBiz source repository](https://github.com/ZedBiz44/z-code-allocation-Skill). Keep implementation, security and rollback, validation, and pilot records in its `docs/` directory. Those operational records are not runtime instructions and are excluded from the generated package.
