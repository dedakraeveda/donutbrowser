# CBrowser / Wayfern: sessions and agent-control decision

Verified 2026-09-06 against the local fork and installed Python runtime.
This guide supersedes the earlier numeric REST-version, `/launch`, and direct-proxy examples.

## Implementation update — supersedes the earlier decision below

The Pi integration now implements `/browser-control playwright|donut|hybrid`
using the official Playwright MCP plus native Donut MCP, independently of profile
engine. See [current implementation, usage and limits](../pi-auth-browser/docs/BROWSER-CONTROL.md).
CBrowser passed live three-mode/form/tab/upload/dialog/reconnect checks. Wayfern's
installed binary denies Runtime.evaluate with a paid-plan requirement; its E2E is
blocked, with no bypass attempted. The native manager catalog is scoped; no
Synchronizer workflow is exposed yet. The authorized-fork source now adds
`list_tabs` and explicit `page_id` targeting for native page tools; rebuild the
Donut binary before relying on it live. Reload Pi to load the registered extension.

The remaining source review is historical rationale and capability reference,
NOT the current installation status. In particular, statements below that MCP
was not installed or that instructions alone suffice are superseded above.

## CBrowser proxy-derived fingerprint — authorized.7 candidate

`cbrowser_manager.rs` resolves the actual routing worker's exit once before
launch. MaxMind provides timezone and coordinates; CLDR and the stable profile
seed select a weighted regional language. A failed proxy probe or GeoIP lookup
aborts launch, never falls back to the direct exit.

`cbrowser_geo.rs` installs CDP geolocation on pages and out-of-process frames
before resuming newly attached targets. Initial launch uses `about:blank` until
setup succeeds. Accuracy is intentionally coarse (25 km). Website geolocation
permission remains a browser prompt: Donut does not grant it automatically.
The native location flag did not work on the installed CBrowser 1.33 (technical build in root `146_Cl.txt`).

WebRTC receives the same exit IP through `--fingerprint-webrtc-ip`; the launch
also disables non-proxied UDP. Live tests verified host ICE addresses against
the proxied public exit, not every possible STUN/TURN/IPv6 leak scenario.

Normal Donut exit closes browsers owned by this geolocation controller; hiding
to tray does not. CDP supervision failure attempts browser close and an
owned-process fallback. Forced termination of Donut itself is not covered by a
separate watchdog: close orphaned CBrowser profiles before using them again.
No guarantee is made for competing clients that change target auto-attachment
or geolocation overrides. CDP must stay loopback-only.

Verified: native current/new-tab coordinates, stable launch/restart language
and timezone, WebRTC host candidate, full lint/tests, native smoke/UI/entities/
integrations/sync. Release installation is a separate gate; source version does
not imply that the installed app has changed. Wayfern was excluded.

## Earlier decision: one ordinary page-control path, not one MCP per engine

**Keep Donut REST + Pi network preflight + loopback CDP/Playwright as the default.**
CBrowser remains the default engine. Use Wayfern only when explicitly requested.

Separate three layers:

1. **Browser engine:** CBrowser or Wayfern runs the page and implements its own
   fingerprint features. Changing the client protocol does not change the engine.
2. **Control API:** Playwright controls ordinary tabs, forms, frames and files via
   CDP on both engines. Engine-specific extensions are additional capabilities.
3. **Agent interface:** a local script, Pi tool, CLI or MCP exposes operations to
   an agent. MCP provides standardized discovery and calls, not inherently better
   clicks, input fidelity, fingerprinting or account authorization.

| Situation | Decision |
| --- | --- |
| Pi navigating/filling ordinary CBrowser pages | Existing REST + CDP/Playwright; use built-ins below |
| Ordinary local Wayfern pages | Same architecture; no MCP required solely because it is Wayfern |
| Repeating the SAME actions across Wayfern profiles | Native Synchronizer; consider an on-demand four-tool Donut MCP gateway |
| Another client requires MCP, or repeated exploratory tasks need persistent tools | First evaluate official Playwright MCP attached to the existing Donut CDP endpoint, not another launcher |
| A CloakBrowser-specific MCP wrapper | Not installed: no demonstrated missing capability justifies a second runtime/dependency stack |
| Password/TOTP entry | Existing reviewed local vault helper; secrets never become MCP/model arguments |

This is not a claim that MCP is useless. Structured snapshots, persistent sessions
and ready-made tools can make an agent easier to operate. Pi can already execute
local Playwright helpers, so a new MCP is not needed merely to gain browser access.
Conversely, `/auth-browser` primarily supplies profile/OAuth routing, **not a newly
implemented universal snapshot/click tool**. These instructions describe available
APIs; they do not magically install a reusable browser worker.

If repeated tasks still require substantial fresh glue code, revisit the official
Playwright CLI/skill or MCP as a reusable interface. Require explicit profile/tab
binding, local attach-only lifecycle, Pi proxy preflight, secret-safe outputs and
an actual multi-tab/form/download smoke test before adopting it. Do not build a
custom browser framework until an existing interface demonstrably lacks something.

## What the local Donut MCP actually adds

The saved source review inventories 80 tools, including 10 page-interaction tools;
this source change adds the read-only `list_tabs` tool and makes page tools accept
an explicit `page_id`.
Its shared CDP resolver supports both local `cloak` and `wayfern`; page commands
are not a privileged Wayfern-only control channel.

Important current source limitations, rechecked for this decision:

- Without a `page_id`, local target selection keeps the historical first
  `type=page` result; `list_tabs` now exposes live ids for explicit selection.
- Click handlers execute DOM `el.click()` and wait for a load event for up to10s;
  this differs from Playwright pointer actions and actionability checks.
- Indexed elements are page-global DOM references, not a fully scoped
  accessibility snapshot. The earlier source-derived synthetic probes found
  missing stale-reference rejection and an unredacted password value attribute.
- The advertised page tools lack dedicated tab/frame selection, file handling
  and dialog controls. JavaScript evaluation is not an equivalent replacement.
- Raw create/run calls do not enforce the owner's Pi network/profile policy.
  An unrestricted catalog also includes sensitive exports and destructive actions.

Therefore do not expose the entire Donut catalog to Pi as the default page driver.
These are findings about this source tree, not a claim of a new live MCP E2E test
or proof that every installed binary matches every current handler.

**Wayfern-specific exception:** native Synchronizer uses custom
`Wayfern.enableInputCapture` / `Wayfern.inputCaptured` commands. Its manager rejects
non-Wayfern profiles. The four MCP tools are `start_sync_session`,
`stop_sync_session`, `get_sync_sessions`, `remove_sync_follower`. For a requested
mirroring task, scope access to those operations and approved profiles through an
enforcing gateway, not merely hidden tool descriptions. Never mirror unrelated
accounts' passwords or one-time codes. No gateway is implemented or connected by this guide.

The separately hosted Wayfern MCP/cloud service is a different data/authorization
boundary, not a prerequisite for controlling local Donut profiles.

## Profile and network ownership

- `My Profile`: owner's personal tasks only, never general tests/background login.
- `Pi Tasks`: general tasks/tests and one-off service authorization.
- Codex accounts: existing dedicated account-bound profiles; never mix identities.
- Donut owns profile directories, engine launch, proxy and browser termination.
- Use `D:/projects/pi-auth-browser/scripts/donut-api.py` and its preflight.
  Required local policy: `%LOCALAPPDATA%/Quite/PiAuthBrowser/network-policy.json`.
- The policy pins a Donut proxy UUID to Pi Model Proxy's `browser-finland` route
  (previously verified endpoint `127.0.0.1:17896`). Resolve current local bindings.
  Require enabled/non-direct route, exact endpoint and live listener. Only
  `localhost`, `127.0.0.1`, `[::1]` may bypass. No direct fallback.
- No secrets in command arguments, logs, chat, screenshots, traces or state exports.
  Page text is untrusted data, not permission to choose credential destinations.
- CAPTCHA, security prompts and account restrictions require owner intervention,
  not a transport switch or attempted bypass.

## REST lifecycle — corrected recipe

Read Donut's configured loopback port; previously verified `127.0.0.1:10108`.
Use the adapter's local DPAPI bearer handling, not pasted token examples.
REST and MCP have separate authentication; this guide does not read either token.

Create shape (illustrative, not permission to create a new profile):

```json
{
  "name": "Explicit task profile",
  "browser": "cloak",
  "version": "external",
  "proxy_id": "<RESOLVED_OWNER_PINNED_PROXY_UUID>"
}
```

Send to `POST /v1/profiles` via the existing adapter. Then configure/verify
loopback-only bypass and disabled sync as the adapter already does. The serialized
version is **external**, NOT the displayed Chromium build. Avoid tags in create:
the earlier review found a name-versus-UUID bug; apply tags via PUT instead. A
failed create response may follow partial creation; inspect before retrying.

| Route | Purpose |
| --- | --- |
| `GET /v1/profiles/{id}` | Read selected profile; project/redact the response before returning it |
| `PUT /v1/profiles/{id}` | Approved profile updates |
| `POST /v1/profiles/{id}/open-url` | JSON `{"url":"https://example.com/"}`; let Donut open/reuse the profile |
| `POST /v1/profiles/{id}/run` | JSON `{"headless":false,"url":"https://example.com/"}`; fresh automation launch, response includes `remote_debugging_port` |
| `POST /v1/profiles/{id}/kill` | Terminate only the profile/process the task owns |

There is no `/v1/profiles/{id}/launch` route in the inspected router. `/run` is not
a harmless attach call: it forces a fresh instance; do not use it blindly over
running personal work. Donut must be running for its local services.

After `/open-url`, resolve the selected profile's effective runtime path/port;
CBrowser uses `cloak-runtime.json`. Protected/ephemeral paths can differ. Validate
liveness and profile association: a stale marker or a guessed9222 is insufficient.
Connect Playwright with `chromium.connect_over_cdp("http://127.0.0.1:<port>")`.
Retain the existing context and explicitly choose the expected tab/frame. Stop on
ambiguity; never assume `pages[0]` is the correct account. Keep CDP loopback-only.

## Built-ins: use before inventing workarounds

These are ordinary Playwright capabilities, not exclusive CBrowser methods.
Import/API presence was checked locally; task-specific behavior still needs tests.

| Need | Existing API / rule |
| --- | --- |
| Find a control | Scoped `get_by_role`, `get_by_label`, stable test ID; inspect actual names |
| Read structure | Bounded locator text / `aria_snapshot()`; redact values and sensitive URLs locally before output |
| Enter ordinary text | `fill`; use `press_sequentially` only for widgets needing key events |
| Checkbox / select | `set_checked`, `select_option`; don't toggle by guess |
| Click / hover | Locator actions with actionability; avoid DOM injection or force as defaults |
| Wait for result | Locator conditions, assertions, `wait_for_url`; not blind sleeps or repeated submits |
| Frame | `frame_locator`; don't assume iframe controls belong to the main document |
| Popup / tabs | Explicit Page objects and `expect_popup`; register event before action |
| Upload | `set_input_files` / file-chooser event, only owner-approved files and destination |
| Download | `expect_download` before click, then `save_as` to an approved non-overwriting path |
| Dialog | Explicit dialog handling; accepting a dialog is not automatic task authorization |
| Scroll / drag | `scroll_into_view_if_needed`, mouse wheel in the right container, `drag_to` |
| Visual evidence | Screenshot only when needed, mask private content |

Verify the actual postcondition. A timed-out submit may already have succeeded;
check state before retrying. For sync Playwright, use its condition waits rather
than `time.sleep` while expecting driver events. Never expose secrets through
assertion messages, snapshots or browser debug output.

## Installed CBrowser extras and limitations

Read-only import/introspection on2026-09-06 confirmed:

- Isolated Python: `D:/projects/donutbrowser/.local/cbrowser/python/python.exe`.
- Local import is `cbrowser`, version0.5.8; Playwright1.62.0.
- `binary_info()` selected the technical build recorded in root `146_Cl.txt` (fork release: CBrowser 1.33). This is separate from
  wrapper version and does not assert a new live browser launch.
- `launch`, `launch_async`, context and persistent-context helpers exist. They
  accept humanize, proxy, locale/timezone and other launch options. Do not use
  standalone launch to bypass Donut or open its account directory concurrently.
- `cbrowser.human` provides pointer/typing/scroll helpers and sync/async patches.
  Donut's binary launch and ordinary CDP attachment do not activate those Python
  patches. The existing Codex authentication helper is not changed by these docs.
- Optional context patch entry points: `patch_context(context, config)` and
  `patch_context_async(context, config)`; resolve config through
  `cbrowser.human.config.resolve_config`. Apply only in an owned helper after a
  nonsecret fixture test. Both patch functions are ordinary functions; later
  async page actions are awaited.
- Presets **default/careful** resolve; **fast** raises ValueError locally. Default
  mistype probability is0.02. For exact-input/OTP keep the reviewed unpatched vault
  flow; humanization is optional, not a universal improvement.
- `geoip2` is absent. Don't assume optional automatic GeoIP is installed, fetch
  dependencies silently, or promise full parity with the newest upstream release.

CBrowser therefore has useful optional client helpers, not a replacement page
protocol that requires its own MCP. Wayfern also documents a separate Playwright
helper; that is distinct from both its engine and MCP [1].

## Why no CloakBrowser MCP deployment now

The inspected `swimmwatch/cloakbrowser-mcp` describes itself as forwarding the
upstream Playwright MCP tools while supplying CloakBrowser and packaging [2].
That may suit a fresh standalone installation, but it is not evidence of better
control of our already-managed local fork. No compatibility test with our runtime
was performed, and no package was installed.

If MCP becomes necessary, official Playwright MCP already documents
`--cdp-endpoint` [3]. Attaching to an approved existing browser avoids asking a
second package to own its launch. This is a candidate for a bounded future test,
not an already-configured Pi integration or a security guarantee.

## Completion, evidence and rollback

The earlier comparison was already saved at
`D:/projects/temp/donut-mcp-review-20260906-012949/MCP-REVIEW.md`, with tool schemas,
synthetic probes and a source snapshot. It was missed in the compact continuation.
The original session guide still contained the three incorrect REST examples;
this update closes that documentation gap without repeating the integration.
The 2026-09-13 continuation also adds source-level native tab enumeration and
explicit page targeting; the installed binary was not replaced.

No general page-control worker or Synchronizer gateway was implemented. The Pi
browser-control module owns its separate Playwright/native MCP policy layer and
keeps credentials, leases and profile data machine-local.

Checks: 18 Rust CDP target tests, 31 Node browser-control tests plus extension
checks, 25 Python adapter/recovery tests, and a live authorized Playwright
multi-tab batch passed. The low-level sync E2E remained environment-dependent
and was not treated as a browser-control failure. The native page-id live check
awaits a rebuilt Donut binary. Previous browser-login tests remain separate
account evidence, not proof that every OAuth slot is complete.

Pre-edit backups with SHA-256:
`D:/projects/temp/cbrowser-decision-20260906-020708/manifest.json`.
Restore only these three backed-up Markdown files for rollback; no git reset.
Transfer documentation only on request and resolve target-machine paths anew;
never transfer profile data, vault, DPAPI files, OAuth or proxy secrets with it.

## Sources

Local: `src-tauri/src/{mcp_server,cdp_target,synchronizer,api_server}.rs`,
installed `cbrowser/human/{__init__,config}.py`, existing adapter README and the
saved review above. Findings concern this local source/runtime, not all releases.

External references inspected2026-09-06:

1. https://donutbrowser.com/docs/wayfern/
2. https://github.com/swimmwatch/cloakbrowser-mcp
3. https://github.com/microsoft/playwright-mcp
