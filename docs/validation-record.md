# z-code-allocation Validation Record

**Status:** Source and static package validation passed. Target-platform pilot remains required before broader deployment.

## Tested Artifact

| Field | Value |
|---|---|
| Tested source commit | `e2e502b16c6d640270fe6bbc2483b8d6b9243708` |
| Runtime artifact | `dist/z-code-allocation/` generated from the tested source commit |
| Test date | 2026-08-17 MDT |
| Result | Passed |

## Commands and Results

- `bash -n scripts/build_package.sh scripts/test_default_package_build.sh` passed.
- `python3 -m py_compile scripts/validate_skill.py` passed.
- `bash scripts/test_default_package_build.sh` built `dist/z-code-allocation/` and passed structural validation.
- `python3 scripts/validate_skill.py dist/z-code-allocation` passed.
- `git diff --check` passed before commit.
- `node --check scripts/request_z_code.mjs` and `python3 -m py_compile scripts/request_z_code.py` passed.

## Remaining Deployment Evidence

- Run the target-platform validator when the pilot environment provides one.
- Install only the generated package on one approved pilot target.
- Record fresh-session discovery plus positive, paraphrased-positive, boundary, and negative trigger outcomes in the pilot record.
- Confirm the installed package matches the tested source commit and that the rollback procedure is executable.
