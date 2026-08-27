# z-code-allocation Validation Record

**Status:** Source, client semantics, and generated-package validation passed. Target-platform pilot remains required before broader deployment.

## Tested Artifact

| Field | Value |
|---|---|
| Tested source commit | `c20e7db37d2271f750d77ef693d4cb0af922a17e` |
| Runtime artifact | `dist/z-code-allocation/` generated from the tested source commit |
| Test date | 2026-08-27 MDT |
| Result | Passed |

## Commands and Results

- `bash -n scripts/build_package.sh scripts/test_default_package_build.sh` passed.
- `python3 -m py_compile scripts/validate_skill.py scripts/request_z_code.py scripts/test_client_semantics.py` passed.
- `python3 scripts/test_client_semantics.py` passed for the Node.js and Python clients.
- The semantic test verified known lookup, exit-zero lookup miss, unknown-status 404, unauthorized 401, server 500, malformed command, transport failure, and secret-safe output.
- `bash scripts/test_default_package_build.sh` rebuilt `dist/z-code-allocation/`, passed structural validation, and reran the client semantics against the generated package.
- `python3 scripts/validate_skill.py dist/z-code-allocation` passed.
- `git diff --check` passed before commit.
- `node --check scripts/request_z_code.mjs` and `python3 -m py_compile scripts/request_z_code.py` passed.

## Repaired Contract

- The runtime guide names the bundled client and the current ZedBiz OpenClaw path.
- Absence from MCP or `ALL_TOOLS` discovery is no longer treated as proof that the bundled client is unavailable.
- Only a `lookup` 404 with allocator code `not_found` becomes exit-zero `found: false`.
- Unknown status requests and authentication, validation, transport, timeout, review, and server failures remain nonzero stop conditions.

## Remaining Deployment Evidence

- Run the target-platform validator when the pilot environment provides one.
- Install only the generated package on one approved pilot target.
- Record fresh-session discovery plus positive, paraphrased-positive, boundary, and negative trigger outcomes in the pilot record.
- Confirm the installed package matches the tested source commit and that the rollback procedure is executable.
