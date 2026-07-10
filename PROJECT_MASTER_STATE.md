# Compatibility Pointer — Project Master State

This root-level legacy filename is not a canonical state authority and must not contain an independent project-state copy.

Canonical human-readable master state:

`06_PROJECT_MASTER_STATE.md`

Primary machine-readable current-state authority:

`PROJECT_RUNTIME.json`

Rules:

- Do not write current runtime status, ERA results, counts, HEAD values, or timestamps into this file.
- Do not use this file as a startup authority.
- Keep this file only for compatibility with older scripts or references.
