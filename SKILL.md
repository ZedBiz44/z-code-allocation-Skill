---
name: z-code-allocation
description: Look up, reserve, confirm, fail, or check authoritative record codes through the configured central allocator.
---

# Code Allocation

Use the configured central allocator whenever a governed knowledge record requires an authoritative code. Never calculate, guess, increment, copy, or reuse a code manually.

## Runtime Client

The allocator is a bundled command-line client, not a separately exposed MCP or `ALL_TOOLS` entry. Absence from a tool registry does not mean the allocator is unavailable.

On ZedBiz OpenClaw runtimes, use:

```bash
ZCODE_CLIENT=/home/node/.openclaw/skills/z-code-allocation/scripts/request_z_code.mjs
test -f "$ZCODE_CLIENT"
```

Other supported packages must run the bundled `scripts/request_z_code.mjs` with Node.js or `scripts/request_z_code.py` with Python from the active skill directory.

Check required configuration without printing any value:

```bash
for name in ZCODE_ALLOCATOR_URL ZCODE_API_KEY ZCODE_AGENT_NAME; do
  if [ -n "$(printenv "$name")" ]; then printf '%s=set\n' "$name"; else printf '%s=missing\n' "$name"; fi
done
```

Do not proceed if any required value is missing.

## Commands

Look up a likely existing identity before allocating:

```bash
node "$ZCODE_CLIENT" lookup --name-key Example-Name-Key
```

A normal miss returns exit `0` with `{"found":false,"name_key":"Example-Name-Key"}`. This means no matching record was found; it is not an outage. Allocate only when record creation is authorized and duplicate checks are complete.

```bash
node "$ZCODE_CLIENT" allocate \
  --request-id agent-20260827-example-name-key \
  --name-key Example-Name-Key \
  --core Z1ST \
  --lane 80001 \
  --page-type Brief
```

Keep the same request ID for every retry of the same allocation. After creating and reading back the final record, confirm it:

```bash
node "$ZCODE_CLIENT" confirm \
  --z-code Z1ST-80001-100001-010 \
  --notion-url https://www.notion.so/example
```

If record creation fails after allocation, mark the code failed instead of recycling it:

```bash
node "$ZCODE_CLIENT" failed \
  --z-code Z1ST-80001-100001-010 \
  --reason "Record creation failed"
```

Check an existing request when reconciling an uncertain retry:

```bash
node "$ZCODE_CLIENT" status --request-id agent-20260827-example-name-key
```

## Workflow

- Determine the proposed name key, owning collection, lane or category, and record type.
- Look up likely existing identities before reserving a new code.
- Treat lookup `found: false` as the decision point to allocate when authorized, not as a failed invocation.
- Allocate before creating the final record and retain the stable request identifier.
- If allocation requires review, stop that record and report the review identifier.
- Create the record with the returned code exactly as issued.
- Verify the stored record and its final type before confirming the allocation.
- If record creation fails, mark the allocation failed with the reason. Never recycle it.

## Stop Conditions

Stop and report the exact failure when the bundled client itself reports missing configuration, authentication or authorization failure, invalid input, review required, transport failure, timeout, or server failure. An unknown `status` request remains an error because it indicates that the supplied request ID was not recorded.

## Runtime Profile

Use the allocator command, endpoint, credentials, classifications, and review owner supplied by the active implementation profile. Never print or store allocator credentials in pages, logs, prompts, or repositories.

## Governance and Operational Records

The authoritative technical copy and current deployment evidence are maintained in the [ZedBiz source repository](https://github.com/ZedBiz44/z-code-allocation-Skill). Keep implementation, security and rollback, validation, and pilot records in its `docs/` directory. Those operational records are not runtime instructions and are excluded from the generated package.
