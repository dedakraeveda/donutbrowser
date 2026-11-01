# Wayfern155 — initial fork/licensing assessment

Status: AUTHORIZED_ADAPTATION_IN_PROGRESS. Original input immutable; no modified
engine or native parity result is claimed yet.

Owner clarification (2026-11-02): after being asked specifically about Wayfern
modification/rebranding/distribution, owner confirmed «да, конечно на wayfern
тоже, давай делать самостоятельно» and delegated REA/tool choice. The decision
is agent-led engineering with REA/Ghidra for bounded native analysis, not a
separate unattended agent or a blind generic unlocker. Permission recorded in
AUTHORIZED_FORK.md; no repeated rights question needed within this scope.
Owner asked to fetch Wayfern first and consider adapting it to our fork and our
licensing. Windows/Linux/macOS release work is paused for this assessment.

## Pinned official input

- Manifest observed in an official managed Pi Tasks browser:
  https://donutbrowser.com/wayfern.json
- Version:155.0.8059.79.
- Advertised slots: Windows x64, Linux x64, macOS ARM64. Linux ARM64,
  Windows ARM64 and macOS x64 were null at this observation. This does not prove
  there are no older builds for those architectures.
- Windows URL (normalized trailing slash):
  https://download.wayfern.com/wayfern-155.0.8059.79_windows_x64.zip
- Bytes:1,599,626,910;2382 files; uncompressed2,670,650,721 bytes.
- SHA256:43925a0841c254f66289565cd1d65f7d783c1f1e40b2a77fd402253c59b3e8b1.
- Published `.zip.sha256` fetched through the same managed browser matches.
  Direct manifest/checksum HTTP calls returned403; the literal manifest archive
  URL ending in `/` returned404, whereas the same archive URL without `/` worked.
  Do not silently patch the manager's resolver based on this single observation.
- Machine-local immutable original:
  D:/projects/temp/wayfern-fork-audit-20261102/original-windows155/
- Original ZIP and evidence DOWNLOAD.json/static-license-strings.json remain in
  that scratch root. Never commit the downloaded engine or place it in release
  kits before redistribution terms are established.

## Actual static observations (not a successful launch)

Printable strings in the original chrome.dll include:

- `Wayfern instance limit reached:` and `browsers are already running on this plan.`
- `wayfern-instance-slot-dir`, `wayfern-token`, `WAYFERN_TOKEN`.
- `Cross-OS fingerprinting requires a paid plan. Provide a wayfernToken parameter.`
- Signed entitlement cache messages and signed-response integrity refusal.
- `https://api.donutbrowser.com/api/auth/wayfern-generate`.
- A launch-identity refusal for a cross-OS claim without a valid paid-plan token.
- Terms acceptance and a separate `license-accepted` marker.

These indicate native gates exist. They do NOT establish exact caps, algorithms,
which launch paths execute them, supported offline lifetime, or successful host-OS
fingerprinting. No cap bypass, forged token, modified signature validation,
license marker fabrication or endpoint impersonation was performed.
No engine executable was launched; terms were not automatically accepted.
No disassembler/debugger was needed for this first public-interface assessment.

## Open manager integration vs closed engine

Our0.36 source already has separate browser engines and an EntitlementsPolicy
adapter for LOCAL manager capabilities. That policy is not the engine authority.

`src-tauri/src/wayfern_manager.rs` currently:

- Gets an authentic Wayfern token through CLOUD_AUTH.
- Refuses a known cross-OS launch without that token
  (`WAYFERN_CROSS_OS_REQUIRES_PLAN`).
- Handles unavailable-plan/identity refusal without silently launching a profile
  with the host identity in place of its requested device.
- Passes identity documents/results and version-specific entitlement-cache flags
  to the engine; includes the token only when available.

`wayfern_terms.rs` requires a real terms-acceptance marker for Wayfern itself.
CBrowser availability permits our local automation service to start independently;
that does not accept Wayfern terms or unlock Wayfern's native paid features.

The original archive includes a large `wayfern_fonts` tree with Windows/macOS
font files. Font redistribution is a SEPARATE permission/notice question, not
inherited automatically from Chromium, Donut or our own product licence.
No full Chromium C++ build source is present in the binary archive. This does not
prove upstream has no available source under a separate agreement.

## Rights boundary to establish

Official public terms: https://wayfern.com/tos (section4).
The page identifies Wayfern as proprietary, restricts redistribution/sublicensing,
reverse engineering and notice changes, and calls for written permission for use
outside the named Donut distribution. These terms are evidence of the public
licence, not an assessment of any separate agreement the owner may hold.

Initial uncertainty was resolved by the owner's explicit Wayfern-specific
confirmation above. The earlier Cloak grant alone was not used as proof.
Preserve public notices and record the owner's separate grant; do not claim it
relicences third-party components or supplies missing native source code.

Donut's open-source licensing and third-party notices also remain applicable;
our commercial product agreement cannot replace the licence of upstream code.
Do not describe the whole bundle as exclusively proprietary code owned by us.

## Recommended own-licence architecture

Preferred route: a vendor-approved OEM/source agreement and a rebuilt engine.

1. Obtain supported engine sources/patchset and all-platform build recipes, OR
   an OEM binary with a documented external entitlement-provider interface.
2. Keep a separate issuer for OUR product grants. Define a versioned capability
   document (product/subject/capabilities/platforms/expiry/concurrency), signed
   using a reviewed standard library; private signing keys only on our server.
   Public verification keys may ship in clients. Do not invent custom crypto.
3. Manager adapter checks our product features and invokes the approved engine
   API. A vendor-signed engine token remains vendor-signed unless a real OEM
   build is explicitly configured to trust OUR issuer. A new server alone does
   not make the current binary trust our signatures.
4. Preserve separation between local capabilities and provider-hosted sync,
   remote browsers/proxies/CAPTCHA services. Our licence does not grant those
   services without an upstream agreement or our own separately deployed backend.
5. Default design decision: no new licensing server merely for personal local
   use. For paid distribution, document offline grace/revocation/seat handling
   explicitly. A local concurrency limit cannot implement cross-device seats by
   itself. Never call a disabled check a deployed licensing service.
6. Keep original licence notices and user-visible terms version/consent. Keep
   vendor engine originals immutable and rollbackable; no installed-profile test.

Alternative while OEM rights/source are unavailable: retain Wayfern unchanged
as an optional externally licensed engine and license only our own product layer,
with its capabilities honestly reported. Keep CBrowser as the already tested
Windows path. Do not substitute old legacy engines for full-feature parity.

## Required verification before any parity claim

- Actual fresh-profile host-OS launch, identity application and CDP form.
- Explicit allowed/refused cross-OS and edited-identity cases, without changing
  the user's requested OS as a hidden fallback.
- Exact-tab targeting, close/relaunch, restoration, persistent fingerprint data.
- Concurrent-profile behavior and cleanup; measure real supported limits rather
  than guessing from strings.
- No token in argv/logs/artifacts; secure approved credential transport review.
- Offline and expired-grant behavior for OUR real licence implementation, if built.
- Equivalent Windows/Linux/macOS checks, correct CPU target and resource/fonts
  notices; no latest macOS x64 build advertised by the current manifest.
- Real vendor-dependent tests only with authentic access supplied through the
  existing approved vault flow, never hardcoded in CI or an archive.

## Current result and rollback

Only downloaded original + static/read-only source analysis, no deployment or
engine changes. Private installed authorized.8 and all profiles untouched.
C:4.82GiB before/after; D:38.15→34.17GiB after ZIP+extraction (~4GiB retained).
No Git mutation or workflow dispatch in this assessment. No rollback required.
