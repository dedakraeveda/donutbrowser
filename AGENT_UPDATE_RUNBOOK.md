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

## Verified personal migration — 2026-11-02 (current)

Owner explicitly requested deploying the ready Windows fork. Installed manager
is now `0.36.0+authorized.9`, source `57bc7c8`, native CI `41507122151`.
Installed SHA256:
- `donutbrowser.exe`: `f748857baf9e6bdf6cd039677bacd23dbdecdde536572394b588321e6d4a00b3`
- `donut-proxy.exe`: `dffe52388bfe5df2ca2642c7b491fb399d41c9636ca2c626fc6714a6a11b4e6d`

Fresh cold private backup:
`D:/projects/temp/donutbrowser-pre-authorized9-backup-20261102-215453`.
49,167 files / 9,383,947,186 bytes independently hash-verified; owner ACL.
Inventory SHA256 `c434156558c64189a1fdba03edf620dc170d1128422fc91721d9e8e9293b6ee9`.
Contains private DPAPI/profile material: never publish or transfer it.

All 34 original profile IDs preserved. Existing CBrowser155 explicit path and
legacy Python selector retained. Own Wayfern155 installed additively on D: at
`.local/wayfern/windows-x64-155.0.8059.79-authorized-local-v1`; production browser
version directory refers to this path. Existing Wayfern profiles were NOT
silently upgraded. Fresh synthetic Mac Wayfern profile through real installed
REST + pinned Pi proxy passed forms/perception11/identity stability, repeated
successfully after a real manager restart; test profile deleted afterwards.
CBrowser155 Pi Tasks browser_control HTTPS/webdriver=false passed after restart.
REST and MCP authenticated healthy. Live PID4992 is historical; re-resolve it.

### Migration findings and mandatory regression checks

- Production periodic unused-browser cleanup is skipped by the E2E harness.
  First deployment therefore exposed a missed destructive path: it treated the
  new unused Wayfern as removable and followed its junction into OUR NEW COPY.
  Original candidate/private backup remained intact. Attempt1 was rolled back.
  Fix57bc7c8 returns before any scan/pruning under manual-browser-update policy;
  targeted regression and successful production restart/engine survival verified.
  Never rely solely on an `e2e` binary to verify maintenance/update behavior.
- Version0.36 re-seals API/MCP tokens with its vault storage. A rollback must
  restore `api_token.dat`, `mcp_token.dat` AND `vault.key` coherently with the
  old binaries/settings/registry from the private backup. Binary-only rollback
  caused an auth mismatch during attempt1; coherent restore resolved it.
  Never print/decrypt keys for reporting, mix vault generations or overwrite
  profile DBs after launch without a fresh snapshot of migrated state.
- Before any automatic cleanup or engine removal, resolve reparse-point targets.
  User/private/external targets must never be traversed for deletion. Our fork
  keeps executable-engine pruning manual; unused engines are rollback assets.

Actual evidence: `D:/projects/temp/donut036-personal-deploy-20261102/`.
Same-machine rollback restores original install binaries and coherent settings/
registry/vault from cold backup after resolving/stopping only the current manager.
Keep old engines and external profile junction target untouched.

## Verified personal migration — 2026-11-01 (historical)

Installed manager is now `0.29.6+authorized.8` (PE FileVersion/ProductVersion
and live REST/MCP checked), with CBrowser `155.0.8059.39.1` selected by the
machine-local `cloak_binary_path` setting. The native runtime is under
`.local/cbrowser/cache/chromium-155.0.8059.39.1` on D:. This is our pinned native
binary fork, not a Chromium C++ source rebuild or an upstream Donut0.36 rebase.

Before deployment, a cold, private same-machine backup was independently
hash-verified: `D:/projects/temp/donutbrowser-pre-authorized8-backup-20261101-220147`
(47,552 files, 8,785,680,136 bytes). Its `BACKUP-VERIFIED.json` and
`files-sha256.jsonl` are private: never include them, profile data or DPAPI material
in a distribution/Git/wiki. All33 registered profile IDs and the external-profile
junction were preserved. Only a Pi Tasks profile was opened for the installed
form/network/fingerprint smoke; personal account profiles were not opened.

Legacy Python wrapper0.5.8 still selects146 intentionally: its Playwright PIPE
route with155 times out. Do not switch `.selected-version` globally and silently
break Python clients. The installed Donut uses TCP/CDP with155 successfully.

Rollback: first re-resolve and verify the installed manager PID/executable and
active profiles (do not use a historical PID blindly), stop only that manager,
then restore `installed-app/donutbrowser.exe`, `installed-app/donut-proxy.exe` and
`app-data/settings/app_settings.json` from this private backup. Keep the old146
runtime intact. Before reverting any profile opened by155, take a fresh copy:
newer Chromium can migrate its databases, so overwriting it is not a binary-only
rollback. Never move or clean the protected external junction target.

Current evidence and limitations:
`projects/donutbrowser/Личная установка authorized.8 и резервная копия.md`
in the managed wiki. Full `pnpm test` is not green (missing offline macOS cargo
dependency); an existing OpenAPI clone-coverage failure is separate from the
780 passing Rust unit tests and19 proxy/15 VPN integration tests. Preserve
manual-only executable updates when eventually porting upstream0.36 changes.

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
