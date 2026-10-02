# A-share research environment

Read README.md, docs/ASHARE_WORKFLOW.md and docs/CLOUD_SETUP.md before changing workflows.
Default timezone: Asia/Shanghai. Default execution: local-paper.

Use bash scripts/run.sh for the project CLI and bash scripts/python.sh PROFILE
for isolated engines. Shell exports in installation do not persist in a new
cloud task; these launchers explicitly select the installed interpreters.

Validation: .venv/bin/python -m pytest -q; .venv/bin/python -m ruff check src tests scripts;
bash scripts/run.sh demo --output artifacts/demo; bash scripts/start.sh.

Keep raw data, filled credentials, broker account details and research outputs
out of git. Never substitute synthetic data for real market evidence. Preserve
point-in-time timestamps, exchange calendars, corporate actions, suspended and
delisted stocks. Record trial counts and out-of-sample results.

The demo is a constrained synthetic main-board simulation. It is not a full
exchange matching engine. No live trading endpoint is implemented. Any future
paper gateway requires an explicit simulation account, market-specific metadata,
connectivity checks, durable storage and reconciliation.

After changing dependency inputs, run bash scripts/lock.sh PROFILE, review the
updated pinned hashes, and install/test the affected profile. Do not silently
skip failed profiles, use --no-deps to mask third-party conflicts, or claim a
cloud environment is published without observing the Cloud UI publication.
