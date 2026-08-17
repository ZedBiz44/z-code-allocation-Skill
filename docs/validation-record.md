# z-code-allocation Validation Record

**Status:** Pending execution after this source-standardization change is committed. Do not claim release readiness until this record contains the tested commit and package evidence.

## Required Commands

`bash scripts/test_default_package_build.sh`

`python3 scripts/validate_skill.py dist/z-code-allocation`

## Required Evidence

- Tested source commit and generated package path.
- Command output showing a successful clean build and structural validation.
- Any target-platform validator output and version, when available.
- Fresh-session discovery and positive, paraphrased, boundary, and negative trigger evidence from the pilot record.
- Rollback readiness evidence for the installed target.
