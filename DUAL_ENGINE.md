# Dual-engine authorized fork

This fork supports two explicitly separate Chromium engines. A profile is pinned
to one engine at creation and never changes engines implicitly.

## Wayfern

Wayfern remains Donut Browser's native engine. It supports Donut's editable
fingerprint model, identity API, cross-OS claims (with a valid external Wayfern
token), native input capture, Cookie Bot/fleet handoff, and synchronizer.

A normal debug run also discovers existing release Wayfern versions under the
standard `DonutBrowser/binaries/wayfern` directory and references them in place.
This fallback is disabled for portable, release, test, and explicitly relocated
data roots so isolated runs never inspect production profile state.

## CBrowser

CBrowser is the bundled autonomous engine for local profiles and local
REST/MCP/CDP automation. The serialized engine id remains `cloak` for backward
compatibility with existing profiles. Each profile receives:

- its own persistent Chromium user-data directory;
- a deterministic `--fingerprint=<seed>` derived from the profile UUID;
- Donut's local SOCKS routing layer, including stored proxies, VPN, VLESS/Xray,
  DNS blocklists, bypass rules, and traffic accounting;
- extension groups, ephemeral/password-protected profiles, clear-on-close, and
  normal profile lifecycle cleanup;
- a loopback-only CDP endpoint usable by Donut MCP or Playwright.

### Portable runtime boundary

The complete workspace-local runtime is stored under `.local/cbrowser` and is
excluded from Git. It includes the browser distribution, isolated CPython,
Playwright, and the wrapper package. Donut discovers that cache automatically
when launched through `dev-local.cmd`. The application-only NSIS bundle does not
embed this ignored runtime and is not a complete portable CBrowser package.

For development or diagnostics, run `cbrowser-local.cmd`. Select a bundled line
persistently with `cbrowser-version.cmd v3` (CBrowser 1.33, default; technical build in root `146_Cl.txt`) or
`cbrowser-version.cmd v2` (legacy Chromium 151, requiring that binary's own valid
authorization state). An optional compatible executable override can be selected
in the Create Profile dialog or provided as `BROWSER_BINARY_PATH`. The override
remains machine-local and is never synced. Complete session examples are in
[CBROWSER_SESSIONS.md](CBROWSER_SESSIONS.md).

## Update boundary

Application self-update is permanently disabled in this authorized build. It
does not query or install releases from the upstream Donut repository. Wayfern
executable/version downloads and GeoIP downloads are also blocked in production;
existing local assets remain usable. Periodic DNS blocklist refresh is disabled,
while an explicit user refresh remains available because the list is
non-executable content. Source, binary, and GeoIP updates are performed only
after an explicit owner request and must follow
[AGENT_UPDATE_RUNBOOK.md](AGENT_UPDATE_RUNBOOK.md).

## Automation

Enable REST API or MCP in **Settings → Integrations**. The same local endpoints
work for Wayfern and CBrowser profiles:

- create/list/get/update/delete profiles;
- run, open URL, kill, and batch run/stop;
- CDP navigation, screenshots, DOM operations, cookies, and humanized input.

For direct Playwright attachment:

```js
const launch = await fetch(`http://127.0.0.1:10108/v1/profiles/${profileId}/run`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ headless: false }),
}).then((response) => response.json());

const browser = await chromium.connectOverCDP(
  `http://127.0.0.1:${launch.remote_debugging_port}`,
);
```

## Deliberate non-combinations

- Fingerprints are never copied between Wayfern and CBrowser.
- Remote fleet sessions and Cookie Bot remain Wayfern-only; silently launching a
  CBrowser profile directory with Wayfern would invalidate its identity.
- Synchronizer remains Wayfern-only because it depends on Wayfern's native
  `Wayfern.inputCaptured` CDP events.
- CBrowser executable overrides are not exposed over REST/MCP: an API token must not be able
  to select an arbitrary local executable.
