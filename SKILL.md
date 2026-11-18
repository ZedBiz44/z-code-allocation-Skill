---
name: z-code-allocation
description: Look up, allocate, rename, or delete authorized knowledge-record codes and verify their registry links.
---

# Code Allocation

Use the configured central allocator whenever a governed knowledge record requires an authoritative code. Never calculate, guess, increment, copy, or reuse a code manually.

Requires allocator 2.2.0 for record administration. Jack authorizes the scope of changes; the configured administrator identity controls these commands. The maintained [Z-Code-Allocation-Skill-SOP](https://app.notion.com/p/3a3a3e33d58180f7bf5ed69f0a398b84) owns the human procedure.

## Runtime Client

The allocator is a bundled command-line client, not a separately exposed MCP or `ALL_TOOLS` entry. Absence from a tool registry does not mean the allocator is unavailable.

Do not assume one fleet-wide installation path. Prefer a `ZCODE_CLIENT` path supplied by the active implementation profile. Otherwise, discover the bundled client from approved skill locations:

```bash
if [ -z "${ZCODE_CLIENT:-}" ]; then
  for candidate in \
    "${OPENCLAW_WORKSPACE:+$OPENCLAW_WORKSPACE/skills/z-code-allocation/scripts/request_z_code.mjs}" \
    "$PWD/skills/z-code-allocation/scripts/request_z_code.mjs" \
    "$PWD/workspace/skills/z-code-allocation/scripts/request_z_code.mjs" \
    "$HOME/.openclaw/workspace/skills/z-code-allocation/scripts/request_z_code.mjs" \
    "$HOME/.openclaw/skills/z-code-allocation/scripts/request_z_code.mjs" \
    "/opt/data/skills/z-code-allocation/scripts/request_z_code.mjs"
  do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
      ZCODE_CLIENT="$candidate"
      break
    fi
  done
fi

if [ -z "${ZCODE_CLIENT:-}" ] || [ ! -f "$ZCODE_CLIENT" ]; then
  printf '%s\\n' "Z-Code client not found in the active implementation profile or approved skill locations." >&2
  exit 1
fi
```

Other supported packages may run `scripts/request_z_code.py` with Python from the active skill directory. Record implementation-specific paths in the deployment profile, not in this universal skill.

Check required configuration without printing any value:

```bash
for name in ZCODE_ALLOCATOR_URL ZCODE_API_KEY ZCODE_AGENT_NAME; do
  if [ -n "$(printenv "$name")" ]; then printf '%s=set\n' "$name"; else printf '%s=missing\n' "$name"; fi
done
```

Do not proceed if any required value is missing.

## Commands

Use the lane and topic rules in [Z-Knowledge-Database-Record-SOP](https://app.notion.com/p/38ca3e33d58180319f0eeada4cf5d5fc). Read the active ranges with `node "$ZCODE_CLIENT" catalogue`. The four-character Z-Knowledge Key selects the range. The issued Z-Code starts with the two-character Knowledge-Family.

- Standard Topic-Names use fixed six-digit Topic-Identifiers in every Knowledge-Lane and Knowledge-Family: Business Overview = `100001`, Website = `100002`, Person = `100003`.
- `100004–100010` are reserved for other shared topics; do not assign meanings to them without Jack's approval. Other new topics start at `100011` and increase within their lane.
- Create a standard topic only when a page needs it. Do not create ten empty topic rows for every lane. Agents select the Topic-Name; the allocator assigns the number. Always use the complete returned Z-Code, including its suffix.

First look up the Name-Key under its Z-Knowledge Key. The result lists the topics inside that lane. The Name-Key belongs to the lane. Each Topic-Name has its own Topic-Identifier within that lane. Keep the same Name-Key when a page needs a different topic in the same lane.

```bash
node "$ZCODE_CLIENT" lookup --folder Z1ZC --name-key Example-Client
```

A normal miss returns exit `0` with `{"found":false,"name_key":"Example-Client"}`. Search for related lanes or topics before asking to create one. Reuse the existing lane and Topic-Name when the subject fits.

```bash
node "$ZCODE_CLIENT" allocate \
  --request-id agent-20261117-example-client-brief \
  --name-key Example-Client \
  --folder Z1ZC \
  --topic-name "Business Overview" \
  --page-type Brief
```

Add `--create-lane` only when a new Knowledge-Lane is needed. Add `--create-topic` only when a new topic is needed within that lane. Omit both flags to reuse existing records. Follow the same command options with the Python client.

Save the Request ID and exact request before sending. The client requires that ID; it never invents one. Keep the same ID and payload for every retry. The client makes at most two transport attempts. After an uncertain result, use status and reconcile; never change the ID to bypass an error. After creating and reading back the final record, confirm it:

```bash
node "$ZCODE_CLIENT" confirm \
  --z-code Z1-40000-100001-010 \
  --notion-url https://www.notion.so/example \
  --record-title "Example Record"
```

If record creation fails after allocation, mark the code failed instead of recycling it:

```bash
node "$ZCODE_CLIENT" failed \
  --z-code Z1-40000-100001-010 \
  --reason "Record creation failed"
```

Check an existing request when reconciling an uncertain retry:

```bash
node "$ZCODE_CLIENT" status --request-id agent-20260827-example-name-key
```

## Workflow

- Determine the Z-Knowledge Key, then check the Name-Key and Knowledge-Lane.
- Within that lane, check the Topic-Name before reserving a new code.
- Treat lookup `found: false` as the decision point to allocate when authorized, not as a failed invocation.
- Allocate before creating the final record and retain the stable request identifier.
- If allocation requires review, stop that record and report the review identifier.
- Create the record with the returned code exactly as issued.
- Read back the original page and verify its exact code, title, URL, Page-Type and required relations before confirming.
- After a publication timeout, find and read the original before trying another create. Unknown outcomes stay unresolved.
- Verify [Z-Code-Registry](https://app.notion.com/p/89267d1e18f84f669269c900dc730b08), [Z-Code-Topic-Registry](https://app.notion.com/p/90ea3e33d58182f1993501fa6e50236f), and [Z-Code-Knowledge-Lane-Registry](https://app.notion.com/p/37ba3e33d581833e8c2781d032f4c6e5) after confirmation. The Code Registry entry's `Topic` links to the specific topic. The topic's `Knowledge-Lane-Record` links to the lane. In the Topic Registry, `Topic-Identity` holds the Topic-Name. A queued mirror still needs verification.
- Check a current code with `node "$ZCODE_CLIENT" resolve --z-code CURRENT-CODE`. Previous codes are stored only in the original page’s `Old-Z-Code` field.
- Only the configured administrator may approve a replacement request after reconciling the original; record the reason and old/new IDs.
- Mark failed only when failure is known and no original page exists. Never mark an uncertain publication failed or recycle its code.

## Corrections And Old-Z-Code

- Before replacing a page’s code, save its current code in that original page’s `Old-Z-Code` field. If that field already contains an earlier code, preserve it and report the difference rather than overwriting it.
- Keep only the current complete code in the allocator and Code Registry. Do not create old-code aliases, redirects, retired-code rows, or a separate history database.
- For later memory updates, read the original page’s `Old-Z-Code` and current `Z-Code`. Clear `Old-Z-Code` only when Jack authorizes it after the memory updates.
- A human-readable Topic Name is separate from the stable Name-Key. Change either only through the allocator's controlled administration route.
- A Name-Key rename keeps the old key as an alias to the same Knowledge-Lane.
- Use the controlled allocator migration operation for a page that belongs in a different topic or lane. The allocator issues the replacement code and removes the superseded Code Registry row.
- After a controlled change, verify the allocator record, the three current registry links, the original page’s Old-Z-Code field, and the original Notion page before reporting completion.
- Do not edit the Notion registries as a reverse-sync method. The allocator is authoritative; Notion is its human-readable mirror.

## Approved Page-Name Corrections

- Use these commands only for an authorized correction. Follow Jack's requirement to show proposed wording before changing it when approval has not already been given.
- Read the current SOP, original Notion page and allocator lane lookup. Identify every original page affected by a lane Name-Key change. Keep their existing Z-Codes and Old-Z-Code fields.
- Rename the original Notion page or pages first. If the Name-Key also changes, use the existing lane operation through this client:

```bash
node "$ZCODE_CLIENT" rename-lane --folder Z1ST --name-key Old-Example --new-name-key Example --reason "Jack approved this lane Name-Key correction"
```

- Then update the allocator Page-Name for each original. The API verifies that the URL belongs to that code and the original page already has the exact requested Page-Name. It keeps the code and queues normal registry updates.

```bash
node "$ZCODE_CLIENT" rename-record --z-code Z1-40001-100011-050 --notion-url ORIGINAL-NOTION-URL --record-title Example-Reference-Check --reason "Jack approved this Page-Name"
```

- Verify the original, allocator Page-Name, lane Name-Key and all three registry links after the mirror finishes. A queued result is not completion. Do not allocate a new code or use confirm as a Page-Name edit.

## Approved Allocation Deletion

- Delete an allocation only when Jack authorized deletion of that exact original or merged copy. Verify useful content is on the kept page and identify its current code before removing the extra page.
- Move the approved extra original to Notion Trash first. Then supply its exact code and original URL. The API refuses a live original, wrong URL or pending registry work.

```bash
node "$ZCODE_CLIENT" delete-record --z-code Z1-40001-100011-050 --notion-url ORIGINAL-NOTION-URL --reason "Jack approved deletion of this merged copy"
```

- A deletion_pending response means the allocator entry is removed but its Code Registry row still needs removal by the mirror. Wait and verify that the registry row is absent or in Trash and the removed code returns 404. Verify the kept original and its code still work.
- Retry an uncertain call with the same code and URL. An already queued deletion returns its pending result. After completed deletion, 404 is expected; verify the registry and kept page rather than treating it as an allocator failure.
- Do not create an alias, redirect, retired-code row, replacement page or separate deletion-history database. The temporary queue entry disappears when mirror deletion succeeds. Do not clear the kept page's Old-Z-Code field without Jack's separate instruction.
- If deletion or its mirror fails, leave the work pending and report the exact error. Do not restore redirects, invent a new code, edit the registries by hand or bypass the API through server/database access.
- The Python helper accepts the same three administration commands and flags.

## Stop Conditions

Stop and report the exact failure when the bundled client itself reports missing configuration, authentication or authorization failure, invalid input, review required, transport failure, timeout, or server failure. An unknown `status` request remains an error because it indicates that the supplied request ID was not recorded.

## Runtime Profile

Use the allocator command, endpoint, credentials, classifications, and review owner supplied by the active implementation profile. Never print or store allocator credentials in pages, logs, prompts, or repositories.

## Governance and Operational Records

The authoritative technical copy and current deployment evidence are maintained in the [ZedBiz source repository](https://github.com/ZedBiz44/z-code-allocation-Skill). Keep implementation, security and rollback, validation, and pilot records in its `docs/` directory. Those operational records are not runtime instructions and are excluded from the generated package.
