# CBrowser fingerprint and geo check — 2026-09-06

## Verified installed Donut path

Two newly created disposable CBrowser profiles used the pinned Pi proxy and loopback-only bypass. Profile A was stopped/restarted through Donut API. Both fixtures were stopped/deleted afterward. Existing profiles and installed binaries were not modified.

Corrected report: `D:/projects/temp/cbrowser-fingerprint-20260906-122540/report.json`.

- Canvas repeatability: passed for all three samples after resetting the canvas before drawing.
- All sampled fields matched across A's restart, including canvas hash and WebGL renderer.
- B differed from A in WebGL renderer and canvas hash. Other sampled values matched. This is not a guarantee of globally unique identities or stability across binary updates.
- All samples reported `navigator.webdriver=false`, Windows platform and the technical Chrome build recorded in root `146_Cl.txt` (fork label: CBrowser 1.33).
- Browser timezone: `Europe/Moscow`; language: `en-US`.
- Two HTTPS egress services observed the same exit IP (only its hash retained). ipwho.is classified it as FI / Europe/Helsinki. This external classification is not yet a comparison with Donut's bundled MaxMind database.
- Earlier report `122359` incorrectly marked repeatCanvasStable=false: its fixture redrew text over the old canvas. Restart hashes still matched. The corrected fixture resets canvas dimensions before drawing; no evidence of engine instability from the earlier faulty test.

## Supported flags verified independently

Installed bundled wrapper `cbrowser/browser.py` maps timezone to `--fingerprint-timezone` and locale to BOTH `--lang` and `--fingerprint-locale`. It resolves GeoIP in the wrapper only when enabled. Donut launches the executable directly, so wrapper GeoIP is not automatically active.

A separate empty temporary headless context used the same installed CBrowser 1.33 executable (technical version in root `146_Cl.txt`) and owner-pinned proxy. No account profile or cookies were used. Explicit Helsinki/fi-FI flags yielded:

- timezone Europe/Helsinki;
- Intl locale fi-FI;
- navigator.language fi-FI; languages [fi-FI];
- webdriver false.

Evidence: `D:/projects/temp/cbrowser-geo-flags-result.json`.
This proves flag support, NOT automatic GeoIP integration or geolocation-coordinate support. At the September test date Helsinki and Moscow both have UTC+3; the timezone ID, not just offset, distinguishes them.

## Implemented source stage (not installed)

`cbrowser_manager.rs::launch` now resolves the exit through the effective proxy supplied by Donut before spawning the browser. It uses the shared proxy URL builder (including SOCKS remote DNS), existing `fetch_public_ip` under a 15-second timeout and bundled MaxMind lookup. Missing/unsupported proxy, failed exit probe, missing/invalid database or invalid timezone abort launch without direct fallback. No IP or credential is logged or persisted by this addition. This also means ordinary CBrowser launches now depend on a working GeoIP lookup; the Donut path supplies a local proxy worker even for a deliberately direct upstream route.

`geolocation.rs::LocaleSelector::locale_for_seed` selects a country-appropriate CLDR-weighted language deterministically from the existing fingerprint seed. Existing random Wayfern selection retains its old behavior. Locale is not persisted; it is stable for the same seed/country/CLDR data, not guaranteed across a changed country or CLDR update. Launch flags are timezone plus both language flags. Coordinates and WebRTC are NOT changed.

Verification: 778 offline lib tests passed; Clippy passed. Three new tests cover deterministic country-scoped selection, flags, missing/invalid timezone/region, missing/unsupported proxy. An explicitly ignored opt-in live test of the actual Rust resolver was run separately through the approved loopback HTTP proxy with `DONUTBROWSER_CACHE_DIR` pointing at the existing Donut MaxMind data. It returned Helsinki/fi-FI on both probes. This is not a full launch E2E. Browser flag behavior was separately tested above. Current installed app and earlier release candidate do not contain this integration. No full frontend/installer build or installation in this stage.

Rollback source only: remove `geo_launch_args`/`resolve_geo_args`, their call/tests, and deterministic locale selector additions; preserve previous fingerprint seed and all unrelated local fork changes. No installed runtime rollback needed.

## Remaining verification and delivery boundary

Reuse Donut's routed exit lookup and bundled MaxMind data, not a second downloaded database or a public geolocation API in production. Resolve through the effective local proxy/VPN worker with bounded timeout and no direct fallback. Supply validated launch flags before process creation; CDP overrides afterward are not equivalent. Preserve profile seed and persist chosen locale rather than randomly changing language across launches (inspect LocaleSelector selection behavior first). Define explicit behavior when GeoIP is missing/unavailable and avoid silently changing existing account profiles. Test proxy change, same-profile restart, no direct fallback, missing database and locale stability, then native Donut launch E2E before release.

Current Donut GUI default change remains source-only in create-profile-dialog.tsx; installed UI and candidate binary predate it. Wayfern investigation remains separate and pending; no further Wayfern creation retries or entitlement changes in this check.
