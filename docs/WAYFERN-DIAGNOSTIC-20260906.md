# Wayfern diagnostic and uninstalled candidate — 2026-09-06

## Scope and findings

- The official source-availability statement distinguishes the AGPL Donut application from the proprietary Wayfern Chromium engine: https://donutbrowser.com/open-source-antidetect-browser/ . Public Donut/humanizer sources are not the engine's C++ source. No engine source was obtained.
- Local source inspection: `cloud_auth.rs::get_wayfern_token` reads the external `DONUT_WAYFERN_TOKEN` override, otherwise its cloud cache. `wayfern_manager.rs` supplies `WAYFERN_TOKEN` to the child and `wayfernToken` to fingerprint/identity commands. Both external/test token environment variables were absent in the diagnostic caller. This does NOT establish the running application's cached-token state.
- Previous direct disposable headless test of installed Wayfern 150.0.7871.102 (reports Chrome/150.0.7871.100) accepted Page navigation, DOM reads and native Input dispatch, but refused Runtime.evaluate with `Browser automation requires a paid Donut Browser plan`. Accepted input commands alone do not prove successful interaction or mirroring.
- Current native Synchronizer diagnostic could not create its first fixture: REST HTTP 400, engine fingerprint generation reported `Too many profiles are being created. Fingerprint generation is temporarily unavailable for this browser.` Further creation attempts stopped once the underlying error was identified. No successful Synchronizer session or live wheel test in this pass. Do not use existing account profiles to avoid this block.

## Source change and verification

`src-tauri/src/synchronizer.rs` maps captured wheel input to `Input.dispatchMouseEvent(type=mouseWheel)` instead of JS `window.scrollBy`. It retains the previous delta sign convention and supplies pointer coordinates and modifiers. Nested-container routing and actual direction still need live validation. Two regression tests check mapping and missing optional fields; these are not E2E tests.

- `cargo test --lib --quiet`: 775 passed.
- `cargo clippy --lib --all-features -- -D warnings -D clippy::all`: passed.
- `cargo build --release --bin donutbrowser --locked`: succeeded; linker warning LNK4075 (MANIFESTINPUT ignored with MANIFEST:NO).
- Existing frontend `dist` reused. This is a Rust release candidate, NOT a full Tauri installer release.
- Full format/lint/test, MinIO suites and native E2E release gates were not completed. Candidate not promoted, installed, or live-tested.

## Artifacts and rollback

`D:/projects/temp/donut-wayfern-candidate-20260906-115943/` contains the previous build artifact, candidate, manifest and pre-build source diff.

Candidate SHA-256: `726d1515b4e7d5b6878891d2903b46cc05c8daf4f8ed08865b9368790476ec99`.
Previous build-artifact SHA-256: `fea1e8c0c46f9dbe68f4d7ebea625e3d5ea8fd618088040066918386aee52005`.

The installed app, engine binaries, credentials, proxies and personal profiles were not replaced. No runtime rollback is required. For source rollback, reverse only this wheel mapping/helper/tests, preserving all pre-existing uncommitted fork changes; do not git reset/restore the repository. The previous build artifact can replace the candidate in `src-tauri/target/release` if needed; it is not asserted to be the currently installed executable.

## Follow-up: running application authorization

Read-only process inspection identified PID 7144, `C:/Users/quite/AppData/Local/Donut/donutbrowser.exe`. Opening its Account page through native accessibility showed **Signed out** and a Sign in button. The standard Donut settings directory contained no cloud auth state/access/refresh files. The inspected application log had no token-acquired or authorization-configured markers; absence of log markers alone is not proof of absent process environment or cache. Reading process environment through Python was unavailable because psutil is not installed; no dependency was installed and no process memory was dumped.

One further owner-requested Synchronizer diagnostic again stopped at fixture creation; its helper withheld the response body, so this follow-up does not independently reconfirm the exact previous fingerprint-rate-limit message. No app sign-in, subscription purchase, credential transfer or installed-binary replacement was performed. Next authorization step requires the owner to identify their Donut account or supply an externally issued token through a private local channel, not chat.

## Next gate

Wait for the fingerprint-creation restriction to clear or obtain vendor clarification; do not retry automatically. Then create two disposable same-OS profiles with the required proxy and test navigation, click, text and wheel mirroring. Resolve legitimate engine authorization through the existing token path if available, or seek a vendor engine fix. No token forgery, binary/license patch or public-source engine rebuild was attempted. Keep CBrowser as the existing Pi/OAuth default.
