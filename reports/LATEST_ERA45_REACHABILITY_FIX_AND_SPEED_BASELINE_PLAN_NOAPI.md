# ERA45 REACHABILITY FIX AND SPEED BASELINE PLAN NOAPI

- Created UTC: 2026-07-08T06:25:00.000000+00:00
- Scope: server-side evidence only.
- No GitHub-side service, timer, DB, nginx, wallet, trade, or provider mutation.

## Aim

Close the active reachability blocker decision path and create the first scientific performance baseline for Tokenoskobi.

## Server-side checks

1. Confirm whether news runner is active/reachable.
2. Confirm whether provider vault is active/reachable.
3. If active, classify as blocked until explicit gate exists.
4. Measure baseline speed without project mutation:
   - Python compile time for selected active tools.
   - JSON parse time for control/public/readmodel files.
   - SQLite read-only pragma and count timing.
   - File scan timing for non-archive repository surface.
   - Public leakage keyword scan timing.
   - Shell/subprocess surface scan timing.
   - Large-file and water-pooling scan timing.

## Output

- JSON report under `data/control/`.
- Markdown report under `reports/`.
- Runtime state advanced to either:
  - `ERA45_CONSOLIDATED_VERIFICATION_REVIEW_NOAPI`, if no active blocker remains.
  - `ERA45_REACHABILITY_FIX_OR_GATE_REQUIRED_NOAPI`, if active blocker remains.

## Rule

Do not start ERA43 real runtime planning until reachability blockers are closed or formally risk-accepted with evidence.
