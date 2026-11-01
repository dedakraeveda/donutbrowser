# Verification and next-update method

## Verified checkpoint (2026-11-02)

Windows manager source commit `294c05a`, native CI run `41480988051`:
frontend/typecheck, Cargo fmt, all-target/all-feature check, four policy tests,
release manager/proxy and native E2E harness build passed. Downloaded ZIP SHA256:
`f16b1399f967dd40e9ccc7e223f861b54b0bbf64721ae7879f3166c789f32583`.
All nine members were independently hashed; PE headers confirmed x64.

A real isolated native WebDriver run of that downloaded harness and the exact
Wayfern native06 candidate passed:

- Generate Mac identity through the manager; update profile through MCP.
- Two simultaneous profiles; actual MacIntel on the claimed Mac profile.
- REST launch + Playwright/CDP form, MCP native form postcondition.
- `Wayfern.capturePagePerception`: 11 fixture nodes (zero is a failure).
- Read profile fingerprint, stop/relaunch; identity fields remain unchanged.
- Stock Wayfern retains the vendor subscription refusal.
- A copied public marker with invalid synthetic EXE/DLL fails closed.
- Wrong MCP token, foreign Origin and stale page fail; manual updates stay off.
- No vendor token flag/env key observed in owned child processes; this is NOT
  a proof of no network calls or a complete secret-transport audit.
- Own test processes absent after cleanup; complete engine hash recheck passed.

Synthetic state/temporary files were on D:, personal installation unchanged.
Official isolated terms acceptance was protected by write-locking the original
personal consent marker and checking its hash/mtime afterwards. Never fabricate
or copy a consent marker. Low-C guard was overridden only by explicit owner
request Telegram9675; this is not a standing permission to ignore disk budgets.

Machine-local evidence (not distribution payload):
`D:/projects/temp/wayfern-fork-audit-20261102/ci-windows-wayfern-macos-fixed-02/RESULT.json`,
`prepare-manager-wayfern-smoke.py`, `manager-wayfern-smoke.mjs`,
`run-ci-smoke.py`, `ci-wayfern-macos-fixed-02.log`.

These are targeted synthetic smoke tests, not the complete upstream E2E suite.
Linux/macOS x64 earlier manager builds passed compilation and policy tests,
not GUI/runtime. ARM64 had no hosted runner on both attempts.

## Repeat on the next update

1. Authenticate the exact upstream archive. Reconstruct source with
   `prepare_ci.py`; all manifest before/after hashes must match.
2. Review every caller of cloud token/OS/fingerprint gates, not just the native
   launch function. The remaining MCP gate was found only by real cross-OS
   testing. Resolve the actual profile before trusting local-engine policy.
3. `wayfern_local_policy` must rehash exact EXE/DLL and validate the marker.
   A marker alone is not authority. Stock retains upstream auth; malformed or
   modified opt-in fails closed, never falls back silently to stock behavior.
4. Preserve token omission for verified local launch/generation/read paths,
   input validation, process cleanup, cohort validation and update guards.
5. Format source, regenerate the changed overlay file, readable patch and its
   `manifest.json` after-hash against the pinned original before-hash. Do not
   normalize exact payload bytes accidentally in Git.
6. Run the native workflow; Windows-only input avoids waiting behind a full
   platform matrix. Verify the run head SHA, build steps, archive/member hashes
   and executable CPU headers. Source-only ZIP is not a binary release.
7. Use existing verified engine without duplicating it: a TEST-ONLY junction
   under isolated `<root>/data/binaries/wayfern/<version>` plus an accurate
   `<root>/data/data/downloaded_browsers.json` fixture. Never point this at the
   personal manager's state, and never delete the junction target.
8. Fresh D: home must use canonical `USERPROFILE/AppData/{Local,LocalLow,Roaming}`.
   Keep per-run WebView, state, cache, TEMP, ports and fixtures isolated.
9. Repeat every assertion above, including cross-OS edit through MCP, actual
   post-navigation navigator state, deterministic relaunch and negative stock/
   tampered fixtures. Merely generating an identity is not enough.
10. Capture resource before/after, verify consent marker unchanged, close only
    owned processes, rehash the actual candidate, and report untested services
    and platforms. Keep prior engine/install/backup for rollback.

The policy CLI reports only its own file-verification scope. Its static
`managerIntegrationVerified: false` is not a runtime health probe; use the
separate actual manager result above. No production installation or complete
browser-kit release is asserted here.
