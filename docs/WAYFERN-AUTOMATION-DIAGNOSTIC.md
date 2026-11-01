# Wayfern 150 automation investigation — 2026-09-06

This is a diagnostic record, not a claim that the engine is repaired.

## Local evidence

- Installed Donut authorized.6 and Wayfern150 DLL hashes match previous
  release/backup records. Donut local automation entitlements are enabled.
- Direct CDP Runtime.evaluate rejects with the paid-plan message. Native Donut
  MCP page-info/content reproduces the rejection without the Pi guard.
- Read-only binary string inspection of installed chrome.dll found the message
  at file offset 0x11165cf8 alongside a source path to
  content/browser/devtools/devtools_session.cc, authorization-service temporary
  failure and automation rate-limit messages.
- Nearby Wayfern strings include VerifyTokenForPlan, signed-response integrity
  validation, request_nonce, token_sha256, WAYFERN_TOKEN and the entitlement cache.
  This supports engine-side authorization checks, but strings alone are not a
  complete control-flow reconstruction or proof of each verification algorithm.
- Donut source already passes externally-issued/cloud WAYFERN_TOKEN into the
  browser environment and wayfernToken into fingerprint/identity operations.
  No supported boolean `isPro` signal was found in the inspected launch code.
- No installed engine binary, signature check, token or entitlement cache was
  modified. No cloud response was forged or service access claimed.

## Source search

Official source boundary: https://donutbrowser.com/open-source-antidetect-browser/
explicitly distinguishes open app/REST/MCP/sync from proprietary Wayfern engine.
The public Donut repository is https://github.com/zhom/donutbrowser .
The separate humanizer library is not the engine source:
https://donutbrowser.com/docs/wayfern/ .
Public searches for WayfernHandler/VerifyTokenForPlan/devtools_session.cc did
not locate the matching engine source. OpenBrowser's repository uses downloaded
Wayfern binaries and is not a source distribution of that engine:
https://github.com/lyu0805/OpenBrowser .

## Synchronizer is a separate test

Earlier broad statements that native Synchronizer could not work before solving
Runtime.evaluate were premature. Real native MCP start_sync_session on two new
empty pinned-proxy Wayfern150 fixtures returned ready. A local HTTP fixture
then proved leader navigation reached the follower (two loads plus follower
CDP target URL match). Both profiles were stopped/deleted afterward.
Native mouse mirroring and scrolling need separate postconditions; ready alone
is insufficient. Source follower replay is fire-and-forget and does not await
CDP errors. Scroll currently uses Runtime.evaluate, so do not extrapolate from
navigation success to full feature support.

Reproducer: ../pi-auth-browser/scripts/diagnose-wayfern-sync.mjs (in the sibling
project; actual invocation from D:/projects/pi-auth-browser).
