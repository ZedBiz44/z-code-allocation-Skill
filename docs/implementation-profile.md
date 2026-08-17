# z-code-allocation Implementation Profile

**Status:** Source package standardized. A target-platform pilot remains required before broader deployment.

## Identity and Ownership

| Field | Value |
|---|---|
| Owner | ZedBiz |
| Canonical identifier | `z-code-allocation` |
| Authoritative source | [z-code-allocation-Skill](https://github.com/ZedBiz44/z-code-allocation-Skill) |
| Runtime package | `dist/z-code-allocation/` |

## Purpose and Scope

Look up, reserve, confirm, fail, or check authoritative record codes through the configured central allocator without manual code creation or reuse.

The skill must stay within the authorization conveyed by its invoking task. It does not grant access, approval, publication authority, or permission to alter unrelated systems.

## Platforms and Packaging

| Field | Requirement |
|---|---|
| Shared core | Codex, OpenClaw, and Hermes-compatible `SKILL.md` frontmatter with `name` and `description` only |
| Build command | `bash scripts/build_package.sh` |
| Structural validation | `python3 scripts/validate_skill.py dist/z-code-allocation` |
| Regression check | `bash scripts/test_default_package_build.sh` |
| Pilot scope | One isolated or explicitly approved target environment before broader rollout |

## Operating Controls

Call the configured allocator with the approved name key, collection, lane, category, record type, and authenticated runtime profile; retain the returned request identifier.

Changes to the skill source, production deployment, privileges, secrets, or external integrations require the approval applicable to that environment. Do not treat this profile as a substitute for environment-specific authorization.

## Completion Evidence

| Evidence | Location |
|---|---|
| Source and static validation | [Validation record](validation-record.md) |
| Security and rollback review | [Security and rollback review](security-rollback-review.md) |
| Pilot and trigger evidence | [Pilot and trigger-test record](pilot-test-record.md) |
| Release source | Git commit and deployment record |
