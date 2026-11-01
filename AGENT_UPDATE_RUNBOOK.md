# Agent Update Runbook — Donut Browser Authorized Fork

Application self-update and executable browser-binary downloads are disabled by design. Automatic background checks, in-app download triggers, and auto-restarts are hard-blocked in code.

GeoIP and DNS blocklists are non-executable data and may refresh automatically with
content validation, atomic replacement, and last-known-good rollback. Their
intervals are runtime-configurable without rebuilding the app:

```text
D:\projects\donutbrowser\set-update-intervals.cmd 12 72
```

The first value is DNS hours; the second is GeoIP hours. The live app reloads the
file within 15 minutes, or immediately after restart. The file is:
`%LOCALAPPDATA%\DonutBrowser\data-update-policy.json`.

Updates MUST be executed manually by an agent ONLY upon explicit user request.

## Mandatory Step-by-Step Procedure

1. **Pre-Update Backup**
   - Create a date-stamped backup of the active app installation and profile data in `D:\projects\temp\donutbrowser-pre-vX-backup-YYYYMMDD`.
   - Record SHA-256 hashes of pre-existing release binaries.

2. **Inspect Upstream / Source Changes**
   - Perform a full `git diff` review before applying updates or pulling branches.
   - Verify that stealth core, local license stripping, local CBrowser resolution, and entitlement policy remain intact.

3. **Enforce Entitlement & Security Policies**
   - Confirm `EntitlementsPolicy::manual_app_updates_only()` remains `true`.
   - Confirm `EntitlementsPolicy::manual_browser_updates_only()` remains `true`.
   - Confirm external data policy permits only GeoIP/DNS data refresh.
   - Ensure `app_auto_updater` and browser-binary background loops remain disabled.
   - Verify no machine-local tokens or credentials are introduced.

4. **Run Verification & Test Suite**
   - `pnpm format`
   - `pnpm lint` (Biome, TypeScript, Clippy, rustfmt, typos)
   - `pnpm test` (all unit & integration checks)
   - Native E2E: `pnpm e2e:smoke`, `pnpm e2e:ui`, `pnpm e2e:entities`, `pnpm e2e:integrations`, `pnpm e2e:sync`
   - Low-level MinIO harness: `pnpm test:sync-e2e` (uses `DONUT_SYNC_TEST_DATA_DIR`)
   - Verify headless Python CBrowser launch and `navigator.webdriver == False`.

5. **Build & Hash Release Artifacts**
   - Build Tauri release target: `pnpm tauri build`.
   - Calculate SHA-256 for `donutbrowser.exe` and `Donut_x64-setup.exe`.
   - Record SHA-256 hashes into the wiki document and release notes.

6. **Documentation & Dashboard Sync**
   - Update `D:\quite\quite\quite\coding\projects\donutbrowser\Donut Browser fork.md`.
   - Update version strings in `package.json`, `Cargo.toml`, `tauri.conf.json`.
   - Run `python D:\projects\project-dashboard\sync.py`.

7. **Post-Update Clean-State Audit**
   - Verify no background processes remain (`minio.exe`, `donut-sync.exe`, `makensis.exe`, `chrome.exe`).
   - Confirm git status is clear of unexpected untracked files.
