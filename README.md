# Code Allocation

This repository is the technical source of truth for `z-code-allocation`, the authoritative workflow for looking up, reserving, confirming, failing, or checking record codes through the configured central allocator.

## When to Use This Skill

- A governed record needs an authoritative code before it can be created or published.
- An allocated code must be confirmed, released, or marked failed through the central service.
- A worker must verify the status of a code instead of guessing or reusing an identifier.

## When Not to Use It

- Invent, reuse, or locally generate a code when the central allocator is available.
- Use the skill for general naming conventions that do not require a tracked record code.
- Continue a record-creation workflow after an allocation error without resolving the authoritative state.

## Authoritative Source and Repository Contents

`SKILL.md` is the authoritative runtime guide. The repository root is the authoritative technical source, while operational SOPs or governed business records remain in their approved operational systems.

- `SKILL.md` is the authoritative runtime guide and defines the skill contract.
- `agents/openai.yaml` provides runtime discovery metadata for supported OpenAI-compatible environments.
- `docs/` records implementation, pilot, validation, deployment, or operational context where applicable.
- `scripts/` contains deterministic validation and, where required, package-build helpers.

## Validation and Deployment

Run the repository validation before release or installation. Build a deployable package only when the target runtime or approved rollout requires one.

```bash
python3 scripts/validate_skill.py .
bash scripts/build_package.sh
python3 scripts/validate_skill.py dist/z-code-allocation
```

Validate on the actual target runtime after installation. Do not assume discovery paths, credentials, or platform behaviour without checking the live environment.

## Safety and Approval Boundaries

Treat allocator responses as the source of truth. Preserve reservation and failure records, do not expose credentials, and stop for clarification when the configured allocator or record type is ambiguous.

## Status and Contributions

Keep this README aligned with the actual skill contract and file structure. Make changes through version control, validate them before release, and document material deployment or governance decisions in the repository’s approved records.
