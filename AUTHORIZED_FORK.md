# Authorized fork: local capabilities

This repository is an authorized fork of Donut Browser. It remains licensed
under AGPL-3.0 and keeps the Donut Browser identity and upstream notices.

The fork enables capabilities that execute entirely on the user's machine. It
does **not** imitate subscriptions, mint cloud credentials, or claim access to
infrastructure operated by Donut Browser or Wayfern.

## Enabled locally

- REST and MCP browser launch/stop automation for Wayfern and Cloak profiles
- profile-pinned Wayfern + bundled CBrowser engine selection
- batch profile launch and stop
- opening URLs in running profiles
- local CDP navigation, screenshots, JavaScript evaluation, clicking and typing
- local synchronizer workflows
- viewing and editing stored fingerprint configuration
- extension and extension-group management through MCP
- unlimited local profiles
- self-hosted sync through the included `donut-sync` service

Local capabilities are enabled by default. To run with upstream-compatible
subscription gates:

```text
DONUT_LOCAL_FEATURES=0
NEXT_PUBLIC_DONUT_LOCAL_FEATURES=0
```

The first variable controls the Rust backend at runtime. The second controls the
frontend at build time. Set both to the same value.

## External Wayfern authorization

Donut's UI and API can allow cross-OS fingerprint configuration, but the
Wayfern browser binary independently validates cross-OS identity application.
If the rightsholder supplied a valid Wayfern token, provide it at runtime:

```text
DONUT_WAYFERN_TOKEN=<externally-issued-token>
```

The token is read from the process environment, is not written to app settings,
and must never be committed. The original fork contract expected local same-OS browser automation to work
without it and only cross-OS identity application to require it.

**Runtime discrepancy (2026-09-06):** the installed Wayfern 150.0.7871.102
rejects local `Runtime.evaluate` and Donut MCP page reads with a paid-plan CDP
error even though this fork's local automation entitlements are enabled.
Installed Donut/Wayfern hashes match previous release/backup records. This is
not a confirmed fix, a requirement to buy a subscription, or evidence that the
new Pi controller introduced the restriction. The earlier same-OS promise is
not currently verified for this binary. CBrowser page automation passes; native
Wayfern Synchronizer end-to-end validation remains outstanding.

## Portable distribution authorization (2026-10-28)

The owner explicitly confirmed: «есть, мне разработчик дал право на форк, но мы же давно собирали эти билды. это далеко не cloak уже давно». This task is authorized to package the existing local CBrowser fork together with Donut for transfer as separate EXE/ZIP artifacts. A shared Chromium version number is not evidence that this binary is an unmodified third-party release. Preserve upstream notices and the applicable source/license materials; do not transfer personal profiles, cookies, vault files or tokens. This confirmation is not a request to update the owner's installed application or accounts.

## Wayfern-specific owner authorization (2026-11-02)

After the agent explicitly asked whether the developer grant also covered
Wayfern engine modification and distribution under our brand, the owner answered:
«да, конечно на wayfern тоже, давай делать самостоятельно». The owner then
left the analysis-tool choice to the agent: «rea или сам ... реши сам».
This records the owner's representation of a separate Wayfern grant, not a claim
that public Wayfern terms or upstream licences have changed. The authorized
scope is isolated engine assessment/adaptation and our own licensing integration;
retain applicable upstream notices and any separately licensed font notices.
Do not impersonate vendor entitlement services or issue vendor credentials.
No personal-profile migration or installed-application replacement is implied.
Original binaries remain immutable; native changes must be exact-hash guarded,
rollbackable, independently tested and reported as binary modifications rather
than Chromium source rebuilds. The current assessment is documented in
`distribution/WAYFERN-FORK-ASSESSMENT.md`.

## Bundled CBrowser engine

CBrowser profiles use the autonomous runtime under `.local/cbrowser`. It contains
the browser distribution, isolated CPython, the Playwright wrapper, and all
required Python dependencies. No system Python or network download is required.
An advanced machine-local executable override may be supplied with:

```text
BROWSER_BINARY_PATH=<path-to-compatible-chromium>
```

The selected override is machine-local and never synced. Bundled lines can be
selected with `cbrowser-version.cmd v3` (autonomous default) or
`cbrowser-version.cmd v2` (legacy line requiring its own valid authorization
state). See [DUAL_ENGINE.md](DUAL_ENGINE.md) for engine boundaries and automation
examples.

## Intentionally cloud-only

These features still require their real service and account entitlements:

- Cookie Bot hosted runs and schedules
- leased remote browser sessions and their CDP relay
- team membership, pooled quotas, and team locks
- Donut-hosted cloud backup
- Donut cloud proxy bandwidth and paid proxy locations
- Wayfern token issuance

Self-hosted sync remains available without Donut cloud login.

## Local automation setup

1. In **Settings → Integrations**, enable REST API and/or MCP.
2. Copy the generated loopback token.
3. REST exposes OpenAPI at `http://127.0.0.1:<api-port>/openapi.json`.
4. MCP listens on its configured loopback port and advertises browser tools via
   `tools/list`.
5. For Wayfern, download a browser version or let a normal debug fork discover
   versions already installed by the release app.
6. CBrowser uses the bundled `.local/cbrowser` runtime by default; selecting an override is optional.

Both servers remain loopback-only and require their generated bearer token.
