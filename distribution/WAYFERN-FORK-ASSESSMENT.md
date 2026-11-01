# Wayfern155 — authorized adaptation and verification

Status: WINDOWS_NATIVE_DIAGNOSTIC_VERIFIED; MANAGER_BUILDS_VERIFIED_3_TARGETS;
FULL_MANAGER_RUNTIME_INTEGRATION_PENDING.
Original input is immutable. The local native candidate is binary-modified,
not rebuilt from Chromium C++ sources and not eligible for production release.

## Current verified checkpoint

- Windows155 candidate `reproduced-native06`: exact DLL SHA256
  `54c30c2a9a73fbc48bb379369c48c1f1f04dc53f3e5d4eada5d57cae40e09185`.
  Native stress evidence: 30 identity generations, 300 CDP operations, six
  concurrent synthetic profiles, cross-OS identity and legacy fingerprint
  replay, negative input refusal and relaunch stability. These are Windows
  tests with simulated device identities, NOT Linux/macOS runtime tests.
- `wayfern_native_policy.py` reproduces only the pinned engine. All 2,381
  original resources are pinned by `wayfern-original-files.json` (including
  DLL/EXE); extra/missing/changed resources fail closed. A rewritten result
  manifest alone cannot authorize an extra file. Failed copies remove only
  their own fresh staging directory. No personal profiles or vendor tokens.
- Policy Python unit tests: **14 PASS**. Real candidate verification: **2,382
  files PASS**, including the added marker (manifest excludes itself).
- Unmodified Rust `wayfern_local_policy.rs` compiled in a bounded isolated
  module harness: **5 PASS**, including matching the actual candidate, missing
  marker stock behavior, false hash claims and oversized/invalid markers.
  Profile lookup is a TEST-ONLY stub: this does NOT verify full Donut compile,
  manager lifecycle, cloud-call omission, REST/MCP or native app E2E.
- Own policy is offline/local, hash-gated. No signed licensing server exists.
  Vendor-hosted services are not granted or impersonated.
- Published resource hardening: `151367f4be09aea6d5056524533659dda0e807d7`.
  All 87 overlay hashes matched. Owner unblocked GitHub Actions; original
  HTTP422 restriction is resolved. Native run41454022962 completed Linux x64
  and macOS x64: TypeScript/frontend build, Cargo fmt, all-target/all-feature
  check, 4 policy unit tests and optimized manager/sidecar build PASS on each.
  Downloaded archives and every member SHA256 verified; executable headers
  confirm ELF64 x86_64 / Mach-O64 x86_64 respectively.
  Linux ZIP SHA256:
  `278e98b180710ffe83258668cd7fd41f4fba2df6eb8fe184c488252f4d24c9d2`.
  macOS x64 ZIP SHA256:
  `11623f7bc944701662bf6035c14be54e5f6f3fd74ae3b1e4544d133ee8fa97d2`.
  These are manager-only binaries, NOT complete browser kits or verified GUI
  runtime. They are retained under the task's D: ci-41454022962-* directories.
  Initial Windows ENV-key casing bug fixed in92a1781; Windows-only matrix
  selection in6de5216. Windows run41461864388 SUCCESS, including full check,
  policy tests, optimized manager/proxy and native E2E harness build.
  Windows ZIP SHA256:
  `6dbb608ba6964fa899a179febd66b4ff0a1b9736625469586de61daaefde109d`.
  All nine members verified, PE headers confirm x64; runtime extracted to
  D:/projects/temp/wayfern-fork-audit-20261102/ci-41461864388-windows/runtime/.
  Fresh isolated D: launch reached native WebDriver session, Donut0.36 startup
  and local MCP listener; test was then STOPPED by disk-resource guard before
  form/MCP/E2E postconditions. C: fell3.32 to2.10GiB; attribution is not proven.
  Task processes were confirmed absent after termination. This is NOT runtime
  smoke PASS and not a Wayfern manager lifecycle test. No more local runs until
  system-disk headroom is restored under a separately authorized operation.
  macOS ARM64 received no hosted runner on BOTH attempts (GitHub capacity
  warning); no ARM64 success or installed-app update claimed.
- Installed authorized.8 and personal browser profiles were not replaced.
  IMPORTANT historical exception: the first official terms command updated
  the existing C: Wayfern consent marker timestamp; exact previous timestamp
  restoration is not proven. Later isolated acceptance protected that marker.
- Current free space after CI download/runtime attempt: C: about2.10GiB,
  D:26.29GiB. Heavy local work is stopped; downloaded artifacts, extracted
  runtime and isolated test state/logs are on D:. Existing user data is not
  authorized for cleanup. Installed personal Donut and private backup retained.

The sections below retain the initial investigation context; statements about
no launch/modification there describe that earlier checkpoint only.

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

See the current verified checkpoint above. The original input, native candidate,
source reconstruction and diagnostics remain on D:. No personal installation
was deployed or migrated. Rollback for local source changes is a reviewed
file-level reversal, preserving unrelated dirty work; do not reset the repo.
Published history is not rewritten. Production release remains blocked on full
manager compile/E2E and native platform build verification.
