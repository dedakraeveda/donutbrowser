# CloakBrowser146: actual public source audit

## What was retrieved

Official repository: https://github.com/CloakHQ/CloakBrowser
Tag: `chromium-v146.0.7680.177.5`
Annotated tag object: `869112adf862b982b462750ba15fc41a7260693e`
Resolved commit: `7e626ee7a1b0e72ab2c9b98315c36302148df1ce`
Source ZIP SHA256: `969f24aa3e6397441e9aea78a1fffedaf218d256fd5e124ad69e3b3c377772d5`.

The downloaded source snapshot has139 ZIP entries and **zero** `.cc`, `.cpp`, `.h`, `.gn`, `.gni`, `.patch` or `.diff` files. It contains Python/JavaScript wrappers, humanization helpers, tests, examples and documentation under MIT. It is not a Chromium checkout or the58 advertised C++ fingerprint patches. GitHub's automatic Source code.zip for this binary release packages the wrapper repository, not the private browser build tree.

Therefore this archive cannot be used to rebuild the exact CloakChromium146 core or replace its private C++ internals with ours. That needs the developer's actual engine source/patchset. Plain upstreamChromium is a different base; recreating equivalent functionality would be a separate large project, not a rename.

## What we replace with our existing code

The compatibility candidate uses **our Donut fork**, not the upstream Python/JS wrapper as a runtime dependency:
- native Donut/Tauri manager, separate app identity/state;
- our CBrowser resolver/defaultrelease1.33 and original technical build mapping;
- persistent per-profile lifecycle and seed;
- our local routing worker, explicit proxy/network settings and fail-closed geo exit lookup;
- our timezone/locale/geolocation supervision and WebRTC launch settings;
- our MCP/REST integrations, explicit page_id/tab selection, humanized native tools;
- our portable launcher, local-secret/user-only setup boundaries, manifests, docs and tests.

Upstream wrapper sources are retained in the audit workspace to compare interfaces and preserve attribution when code is actually reused. They are not relabelled as a new C++ implementation. The engine binary is kept byte-for-byte unmodified and explicitly attributed in ENGINE-PROVENANCE.json and licenses. There is no decompilation, license-token forging, removal of notices, or claimed patch of the closed core.

## Exact platform availability at the audited tag

| Platform | Actual binary version | Official release asset |
| --- | --- | --- |
| Linux x64 |146.0.7680.177.5 | `cloakbrowser-linux-x64.tar.gz` at the146 tag |
| Windows x64 |146.0.7680.177.5 | `cloakbrowser-windows-x64.zip` at the146 tag |
| macOS arm64 |145.0.7632.109.2 | separate145 tag, as pinned by that same wrapper config |
| macOS Intel x64 |145.0.7632.109.2 | separate145 tag, as pinned by that same wrapper config |

The146 release has Linux/Windows binaries, checksums and signature, **no macOS146 asset**. macOS is not silently assigned Linux's version. Our product release label1.33 is separate from these technical versions; original values remain in provenance/root146_Cl.txt.

## Verification and license boundaries

Downloaded Linux archive SHA256 `4a12bcde95fa1bb1beef2b41ab5e5c27c36be78e3be3d0dac8c64d705216670e` matches published SHA256SUMS from the same release. This establishes byte integrity against the retrieved manifest, not an independent signature/attestation check. The downloaded source commit/tag is pinned; no automatic upgrades are used.

Keep wrapper MIT and separate browser BINARY-LICENSE notices. The owner's prior developer permission for the existing local fork is recorded in AUTHORIZED_FORK.md; this audit does not pretend the public wrapper license is also the license of a newly downloaded engine. Compatibility packages must identify that upstream engine, our actual modified layer, and their local-validation scope rather than present them as a source-rebuilt browser core.

## Primary sources

- https://github.com/CloakHQ/CloakBrowser/tree/7e626ee7a1b0e72ab2c9b98315c36302148df1ce
- https://github.com/CloakHQ/CloakBrowser/releases/tag/chromium-v146.0.7680.177.5
- https://github.com/CloakHQ/CloakBrowser/blob/7e626ee7a1b0e72ab2c9b98315c36302148df1ce/cloakbrowser/config.py
- https://github.com/CloakHQ/CloakBrowser/releases/tag/chromium-v145.0.7632.109.2
- https://github.com/CloakHQ/CloakBrowser/blob/7e626ee7a1b0e72ab2c9b98315c36302148df1ce/LICENSE
- https://github.com/CloakHQ/CloakBrowser/blob/7e626ee7a1b0e72ab2c9b98315c36302148df1ce/BINARY-LICENSE.md
