<div align="center">
  <img src="assets/logo.png" alt="Donut Browser Logo" width="150">
  <h1>Donut Browser</h1>
  <strong>Open Source Anti-Detect Browser</strong>
  <br>
  <a href="https://donutbrowser.com">donutbrowser.com</a>
</div>
<br>

<p align="center">
  <a style="text-decoration: none;" href="https://github.com/zhom/donutbrowser/releases/latest" target="_blank"><img alt="GitHub release" src="https://img.shields.io/github/v/release/zhom/donutbrowser">
  </a>
  <a style="text-decoration: none;" href="https://github.com/zhom/donutbrowser/issues" target="_blank">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat" alt="PRs Welcome">
  </a>
  <a style="text-decoration: none;" href="https://github.com/zhom/donutbrowser/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg" alt="License">
  </a>
  <a style="text-decoration: none;" href="https://github.com/zhom/donutbrowser/network/members" target="_blank">
    <img src="https://img.shields.io/github/forks/zhom/donutbrowser?style=social" alt="GitHub forks">
  </a>
</p>

<img alt="Donut Browser Preview" src="assets/donut-preview.png" />

## Portable Agent Kit (Windows x64)

The owner-authorized local Donut/CBrowser transfer kit is documented in [`distribution/START_HERE.md`](distribution/START_HERE.md). Separate NSIS EXE and portable ZIP include the complete local CBrowser **1.33** engine (technical build mapping: root `146_Cl.txt`), matching proxy sidecar, clean source snapshot, offline launcher, licenses and instructions for multiple coding agents. No owner profiles/cookies/tokens are exported. The kit has a separate application identity and does not update the owner's installed Donut. Technology attribution and our packaging changes: [`distribution/STACK.md`](distribution/STACK.md); agent setup: [`distribution/CLIENTS.md`](distribution/CLIENTS.md). Exact hashes/runtime checks and known baseline test limitations are recorded in each release's external `VERIFICATION.md`.

### Linux x86_64 build

Native Linux packaging and prerequisites are documented in [`distribution/LINUX.md`](distribution/LINUX.md). The original Ubuntu 26.04/glibc 2.43 artifact remains explicitly **app-only**, without an engine. A separate, explicitly attributed [Linux upstream146 compatibility candidate](distribution/LINUX-CANDIDATE.md) now bundles our Donut integration with an **unchanged official upstream engine**, pinned hashes and original notices. The final candidate passed native manager → MCP81 tools → fresh browser profile → local form postcondition, plus696 manifest checks and19 native proxy integration tests. It is not a source-rebuilt Chromium core or a generic Debian/Astra build.

[Public146 source audit](distribution/UPSTREAM-146-AUDIT.md): the pinned GitHub tag contains Python/JS wrappers, not Chromium C++ sources/patches. [macOS preparation](distribution/MACOS.md) includes a complete prepared source ZIP, a native Swift launcher and manual Intel/AppleSilicon workflow, but **no verified macOS binary yet**. The146 tag has no Mac assets; explicit legacy mode uses upstream145 with provenance instead of silently relabelling it146. Native Mac/Windows workflows are manual, manager-only by default, and do not publish public releases or update an installed application. [Fresh Windows/engine status](distribution/WINDOWS-NATIVE.md): current upstream155/156 requires a local official key/distribution; no146-to155 relabelling or claimed transfer of unavailable private C++patches.

## Features

- Unlimited browser profiles: each fully isolated with its own fingerprint, cookies, extensions, and data
- Anti-detect Chromium engine: powered by [Wayfern](https://wayfern.com), a privacy-focused Chromium fork whose fingerprint spoofing is not detected by Cloudflare, reCaptcha v3, or other browser fingerprinting and anti-bot services
- DNS AdBlocker: block ads, trackers, and other unwanted content with per-profile DNS blocking
- Proxy support: HTTP, HTTPS, SOCKS4, SOCKS5 per profile, with dynamic proxy URLs
- VPN support: WireGuard configs per profile
- Local API & MCP: REST API and [Model Context Protocol](https://modelcontextprotocol.io) server for integration with Claude, automation tools, and custom workflows
- Profile groups: organize profiles and apply bulk settings
- Import profiles: migrate from Chrome, Edge, Brave, or other Chromium browsers
- Cookie & extension management: import/export cookies, manage extensions per profile
- Default browser: set Donut as your default browser and choose which profile opens each link
- Cloud sync: sync profiles, proxies, and groups across devices (self-hostable)
- E2E encryption: optional end-to-end encrypted sync with a password only you know
- Zero telemetry: no tracking or device fingerprinting

## Install

<!-- install-links-start -->
### macOS

| | Apple Silicon | Intel |
|---|---|---|
| **DMG** | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_aarch64.dmg) | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_x64.dmg) |

Or install via Homebrew:

```bash
brew install --cask donut
```

### Windows

[Download Windows Installer (x64)](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_x64-setup.exe) · [Portable (x64)](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_x64-portable.zip)

### Linux

| Format | x86_64 | ARM64 |
|---|---|---|
| **deb** | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_amd64.deb) | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_arm64.deb) |
| **rpm** | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut-0.29.5-1.x86_64.rpm) | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut-0.29.5-1.aarch64.rpm) |
| **AppImage** | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_amd64.AppImage) | [Download](https://github.com/zhom/donutbrowser/releases/download/v0.29.5/Donut_0.29.5_aarch64.AppImage) |
<!-- install-links-end -->

Or install via package manager:

```bash
curl -fsSL https://donutbrowser.com/install.sh | sh
```

<details>
<summary>Troubleshooting AppImage</summary>

If the AppImage segfaults on launch, install libfuse2 (`sudo apt install libfuse2` / `yay -S libfuse2` / `sudo dnf install fuse-libs`), or bypass FUSE entirely:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./Donut.Browser_x.x.x_amd64.AppImage
```

If that gives an EGL display error, add `WEBKIT_DISABLE_DMABUF_RENDERER=1` or `GDK_BACKEND=x11` to the command above. If issues persist, the .deb and .rpm packages are more reliable.

</details>

### Nix

```bash
nix run github:zhom/donutbrowser#release-start
```

## Authorized Fork: Local Capabilities

This fork enables local REST/MCP/CDP automation, batch profile control, local fingerprint configuration, extension management, and self-hosted sync without a Donut cloud subscription. It supports profile-pinned Wayfern and the bundled autonomous CBrowser engine. Cloud-hosted Cookie Bot, remote browser sessions, team services, hosted backup, proxy bandwidth, and Wayfern token issuance still require their real services.

See [AUTHORIZED_FORK.md](AUTHORIZED_FORK.md) for the capability matrix, [DUAL_ENGINE.md](DUAL_ENGINE.md) for the Wayfern + CBrowser architecture, [CBROWSER_SESSIONS.md](CBROWSER_SESSIONS.md) for UI/REST/Python session setup, and [AGENT_UPDATE_RUNBOOK.md](AGENT_UPDATE_RUNBOOK.md) for the mandatory agent-only update procedure.

## Self-Hosting Sync

Run your own sync server to sync profiles, proxies, and groups across devices for free. See the [Self-Hosting Donut Sync guide](https://donutbrowser.com/docs/self-hosting) for Docker-based setup instructions.

## Contributing

Donut Browser is built by the people who use it, and plenty of the most useful help involves no code at all.

- Tell other people about Donut. Word of mouth is how most users find the project, so talking about it is a real contribution.
- Report bugs and request features in [GitHub Issues](https://github.com/zhom/donutbrowser/issues).
- Answer questions in [GitHub Discussions](https://github.com/zhom/donutbrowser/discussions).
- Fix and improve translations in `src/i18n/locales`.
- Write code. Start with [CONTRIBUTING.md](CONTRIBUTING.md).
- Star the repo so more people see it.

## Star History

<a href="https://gitdebt.com/zhom/donutbrowser?ref=readme">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.gitdebt.com/api/repos/zhom/donutbrowser/chart.svg?theme=dark&animate=1" />
    <img alt="Cumulative GitHub stars for zhom/donutbrowser over time" src="https://api.gitdebt.com/api/repos/zhom/donutbrowser/chart.svg?theme=light&animate=1" />
  </picture>
</a>

## Contributors

<a href="https://gitdebt.com/zhom/donutbrowser?ref=readme">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.gitdebt.com/api/repos/zhom/donutbrowser/stats/contributors.svg?theme=dark&animate=1" />
    <img alt="Everyone who has landed commits in zhom/donutbrowser, ranked by commit count" src="https://api.gitdebt.com/api/repos/zhom/donutbrowser/stats/contributors.svg?theme=light&animate=1" />
  </picture>
</a>

## Contact

For urgent questions or security vulnerability reports, email [contact@donutbrowser.com](mailto:contact@donutbrowser.com).

## License

This project is licensed under the AGPL-3.0 License. See the [LICENSE](LICENSE) file for details.
