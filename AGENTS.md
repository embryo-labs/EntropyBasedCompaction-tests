# tests instructions

Prefer reusing the existing scripts, helper functions, and workload wrappers under `tests/` instead of hand-assembling equivalent command-line parameters. For temporary experiment variations, prefer calling the existing helper/function chain and appending extra db_bench parameters through its normal trailing-argument passthrough.
