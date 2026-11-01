"""Build a clean, source-matching Donut/CBrowser transfer kit without personal state."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

REPO = Path(__file__).resolve().parents[1]
WORK = Path("D:/projects/temp/donut-agent-kit-20261028")
SOURCE = WORK / "source"
PAYLOAD = WORK / "payload-cbrowser-1.33"
TARGET = REPO / "src-tauri/target"
CBROWSER_RELEASE = "1.33"
TECHNICAL_VERSION = (REPO / "146_Cl.txt").read_text(encoding="utf-8").splitlines()[0]
ENGINE = REPO / ".local/cbrowser/cache" / ("chromium-" + TECHNICAL_VERSION)
RELEASE = REPO / ".local/releases/agent-kit-cbrowser-1.33"
VERSION = "0.29.6-authorized.7-kit1"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def budget():
    values = {p: round(shutil.disk_usage(p).free / 2**30, 2) for p in ["C:/", "D:/"]}
    print("FREE_GIB", json.dumps(values), flush=True)
    if values["D:/"] < 15:
        raise RuntimeError("Need 15 GiB free on D for bounded build")
    return values


def env():
    result = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in
              ["TOKEN", "PASSWORD", "SECRET", "API_KEY", "DONUT_", "NEXT_PUBLIC_", "GITHUB_", "BROWSER_", "AWS_"])}
    temp = WORK / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    toolchain = WORK / "msvc/env.json"
    if toolchain.is_file():
        for key, value in json.loads(toolchain.read_text(encoding="utf-8")).items():
            if key in {"PATH", "INCLUDE", "LIB", "LIBPATH"}:
                result[key] = ";".join(value) + (";" + result.get("PATH", "") if key == "PATH" else "")
            elif key in {"CC", "CXX", "AR", "VCINSTALLDIR", "VCToolsInstallDir", "WindowsSDKDir"}:
                result[key] = value
    result.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
                  CARGO_TARGET_DIR=str(TARGET), CARGO_NET_OFFLINE="true", CARGO_BUILD_JOBS="1",
                  NEXT_TELEMETRY_DISABLED="1", PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD="1",
                  BUILD_TAG=VERSION, NEXT_PUBLIC_DONUT_LOCAL_FEATURES="1",
                  DONUT_SYNC_TEST_DATA_DIR=str(WORK / "sync-tests"),
                  pnpm_config_verify_deps_before_run="warn",
                  npm_config_store_dir="D:/.pnpm-store",
                  npm_config_manage_package_manager_versions="false")
    return result


def run(name, command, cwd=SOURCE):
    log = WORK / (name + ".log")
    print("RUN", name, flush=True)
    with log.open("w", encoding="utf-8") as stream:
        status = subprocess.run([str(p) for p in command], cwd=cwd, env=env(),
                                stdout=stream, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW).returncode
    print("RESULT", name, status, str(log), flush=True)
    if status:
        raise RuntimeError(f"Stage {name} failed; inspect bounded log")


def prepare():
    budget()
    WORK.mkdir(parents=True, exist_ok=True)
    if SOURCE.exists():
        raise FileExistsError("Source snapshot exists; do not overwrite")
    names = subprocess.check_output(["git", "-C", str(REPO), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).decode().split("\0")
    allowed_tops = {"src", "src-tauri", "scripts", "patches", "public", "assets", "e2e", "donut-sync", "donut-browser-daemon", "distribution"}
    blocked_parts = {"node_modules", "target", ".next", "__pycache__", "test-results", "artifacts", ".driver", ".git", "runtime", "data", "logs", "profiles", "cache", "backups"}
    for name in sorted(set(names)):
        if not name:
            continue
        relative = Path(name)
        if relative.name.startswith(".env") or relative.name in {"TASK-STATE.md", "CLAUDE.md"}:
            continue
        if len(relative.parts) > 1 and relative.parts[0] not in allowed_tops:
            continue
        if any(part in blocked_parts for part in relative.parts):
            continue
        path = REPO / relative
        if not path.is_file() or path.is_symlink() or path.suffix.lower() in {".exe", ".dll", ".pdb", ".log", ".session", ".zip"}:
            continue
        target = SOURCE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # Bundle identity is separate from the owner's manager: no shared single-instance lock/WebView store.
    config = SOURCE / "src-tauri/tauri.conf.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    data["identifier"] = "com.donutbrowser.agentkit"
    data["productName"] = "Donut Agent Kit"
    config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    binaries = SOURCE / "src-tauri/binaries"
    binaries.mkdir(exist_ok=True)
    for name in ["donut-proxy-x86_64-pc-windows-msvc.exe", "xray-x86_64-pc-windows-msvc.exe", "xray-LICENSE.txt"]:
        shutil.copy2(REPO / "src-tauri/binaries" / name, binaries / name)
    # Fresh public license notice; no owner .env is read or copied.
    for rel in ["node_modules", "donut-sync/node_modules"]:
        dest = SOURCE / rel
        origin = REPO / rel
        if origin.exists():
            subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(dest), str(origin)], check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE)
    # Keep previous target release artifacts intact for rollback (not the installed application).
    backup = WORK / "previous-target"
    backup.mkdir()
    for name in ["donutbrowser.exe", "donut-proxy.exe"]:
        shutil.copy2(TARGET / "release" / name, backup / name)
    print("Prepared clean source snapshot; owner runtime/config excluded", flush=True)


def build():
    budget()
    node = shutil.which("node")
    # Carry the reviewed generated license inventory with the exact source/lock snapshot.
    # pnpm11 cannot regenerate it from this existing store: missing package index metadata.
    inventory = json.loads((SOURCE / "src/generated/licenses.json").read_text(encoding="utf-8"))
    if not isinstance(inventory, list) or not inventory:
        raise RuntimeError("Reviewed third-party license inventory missing")
    run("frontend", [node, "node_modules/next/dist/bin/next", "build", "--webpack"])
    run("cargo-release", ["cargo", "build", "--release", "--locked", "--offline", "--bin", "donutbrowser"], SOURCE / "src-tauri")
    # Avoid the existing thin-LTO cross-crate sidecar link failure; still a release/opt-level3 build.
    run("cargo-proxy", ["cargo", "rustc", "--release", "--locked", "--offline", "--bin", "donut-proxy", "--", "-C", "lto=off"], SOURCE / "src-tauri")
    version = subprocess.check_output([str(TARGET / "release/donut-proxy.exe"), "--version"], text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
    if version != "donut-proxy " + VERSION:
        raise RuntimeError("Matching proxy sidecar build required")
    budget()


def package():
    budget()
    if PAYLOAD.exists() or RELEASE.exists():
        raise FileExistsError("New payload/release already exists")
    actual = subprocess.check_output([str(TARGET / "release/donut-proxy.exe"), "--version"], text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
    if actual != "donut-proxy " + VERSION:
        raise RuntimeError("Refusing mixed-version sidecar payload")
    PAYLOAD.mkdir()
    app = PAYLOAD / "app"
    app.mkdir()
    shutil.copy2(TARGET / "release/donutbrowser.exe", app / "donutbrowser-kit.exe")
    shutil.copy2(TARGET / "release/donut-proxy.exe", app / "donut-proxy.exe")
    shutil.copy2(SOURCE / "src-tauri/binaries/xray-x86_64-pc-windows-msvc.exe", app / "xray.exe")
    (app / ".portable").write_bytes(b"")
    shutil.copytree(ENGINE, PAYLOAD / "cbrowser")
    shutil.copy2(REPO / "146_Cl.txt", PAYLOAD / "146_Cl.txt")
    # A Chromium distribution is executable/resources only: reject any accidental user data.
    forbidden = {"Default", "User Data", "Local State", "Cookies", "History", "Login Data", "Preferences"}
    if any(p.name in forbidden for p in (PAYLOAD / "cbrowser").rglob("*")):
        raise RuntimeError("Unexpected browser user data in engine distribution")
    # Public, non-executable data, selected by exact path; no other cache/state is read.
    assets = PAYLOAD / "assets"
    assets.mkdir()
    city = Path(os.environ["LOCALAPPDATA"]) / "DonutBrowser/GeoLite2-City.mmdb"
    if b"\xab\xcd\xefMaxMind.com" not in city.read_bytes()[-131072:]:
        raise RuntimeError("GeoIP data validation failed")
    shutil.copy2(city, assets / "GeoLite2-City.mmdb")
    docs = PAYLOAD / "docs"
    docs.mkdir()
    for name in ["AGENT-GUIDE.md", "CLIENTS.md", "STACK.md", "RELEASE-CHECKLIST.md"]:
        shutil.copy2(REPO / "distribution" / name, docs / name)
    shutil.copy2(REPO / "distribution/START_HERE.md", PAYLOAD / "START_HERE.md")
    shutil.copy2(REPO / "distribution/AGENTS.md", PAYLOAD / "AGENTS.md")
    shutil.copy2(REPO / "LICENSE", PAYLOAD / "LICENSE-Donut-AGPL-3.0.txt")
    licenses = PAYLOAD / "licenses"
    licenses.mkdir()
    shutil.copy2(REPO / "src-tauri/binaries/xray-LICENSE.txt", licenses / "Xray-core-LICENSE.txt")
    shutil.copy2(REPO / "AUTHORIZED_FORK.md", licenses / "AUTHORIZED_FORK.md")
    shutil.copy2(REPO / "distribution/Chromium-LICENSE.txt", licenses / "Chromium-LICENSE.txt")
    (licenses / "GeoLite2-NOTICE.txt").write_text("This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com. Upstream data source used by Donut: https://github.com/P3TERX/GeoLite.mmdb. GeoLite terms: https://www.maxmind.com/en/geolite2/eula . This is public IP geolocation reference data, not the owner's browsing or account data. Accuracy/freshness is not guaranteed; the app has its own validated non-executable data refresh policy.\n", encoding="utf-8")
    shutil.copy2(SOURCE / "src/generated/licenses.json", licenses / "third-party-inventory.json")
    # Compile the small offline entrypoint; no Python/Node/Rust needed on recipient PC.
    run("launcher", ["C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe", "/nologo", "/target:winexe",
                     "/reference:System.Web.Extensions.dll", "/reference:System.Windows.Forms.dll",
                     "/out:" + str(PAYLOAD / "Donut Agent Kit.exe"), REPO / "distribution/Launcher.cs"])
    (PAYLOAD / "Open instructions.cmd").write_text('@echo off\r\nstart "" "%~dp0START_HERE.md"\r\n', encoding="ascii")
    # Matching source, excluding all build outputs, tool junctions, private files and sidecar binaries.
    with zipfile.ZipFile(PAYLOAD / "Donut-Agent-Kit-source.zip", "x", zipfile.ZIP_DEFLATED) as archive:
        for folder, directories, names in os.walk(SOURCE):
            directories[:] = [n for n in directories if n not in {"node_modules", ".next", "dist", "target", "gen", ".cache", ".driver", "__pycache__"}]
            for name in names:
                path = Path(folder) / name
                rel = path.relative_to(SOURCE)
                if path.suffix.lower() not in {".exe", ".dll", ".pdb", ".log", ".tsbuildinfo"}:
                    archive.write(path, rel.as_posix())
    # Enumerate shipped files, not state: uninstall preserves every non-shipped user file.
    uninstall = ['  Delete "$INSTDIR\\\\MANIFEST.json"', '  Delete "$INSTDIR\\\\uninstall-files.nsh"']
    for path in sorted(PAYLOAD.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(PAYLOAD)).replace('$', '$$')
            uninstall.append('  Delete "$INSTDIR\\\\' + rel + '"')
    for path in sorted((p for p in PAYLOAD.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        uninstall.append('  RMDir "$INSTDIR\\\\' + str(path.relative_to(PAYLOAD)).replace('$', '$$') + '"')
    (PAYLOAD / "uninstall-files.nsh").write_text("\n".join(uninstall) + "\n", encoding="utf-8")
    manifest = {"version": VERSION, "ownerAuthorization": "2026-10-28; AUTHORIZED_FORK.md",
                "appIdentity": "com.donutbrowser.agentkit", "engine": "CBrowser " + CBROWSER_RELEASE, "technicalVersionFile": "146_Cl.txt",
                "gitCommit": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
                "note": "Rebuilt clean source snapshot including local reviewed changes, not an upstream release; no owner profile state",
                "files": {p.relative_to(PAYLOAD).as_posix(): digest(p) for p in sorted(PAYLOAD.rglob("*")) if p.is_file()}}
    (PAYLOAD / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    RELEASE.mkdir(parents=True)
    zpath = RELEASE / ("Donut-Agent-Kit-CBrowser-" + CBROWSER_RELEASE + "-windows-x64.zip")
    with zipfile.ZipFile(zpath, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(PAYLOAD.rglob("*")):
            if path.is_file():
                archive.write(path, "Donut-Agent-Kit/" + path.relative_to(PAYLOAD).as_posix())
    # NSIS offline installer uses exactly the same payload; uninstall intentionally retains state.
    run("installer", ["C:/Users/quite/AppData/Local/tauri/NSIS/Bin/makensis.exe", "/V2",
                       "/DPAYLOAD=" + str(PAYLOAD), "/DOUTPUT=" + str(RELEASE / ("Donut-Agent-Kit-CBrowser-" + CBROWSER_RELEASE + "-setup.exe")),
                       REPO / "distribution/installer.nsi"])
    hashes = {p.name: digest(p) for p in RELEASE.iterdir() if p.is_file()}
    (RELEASE / "SHA256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps({"release": str(RELEASE), "sha256": hashes}, indent=2), flush=True)
    budget()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "build", "package"])
    args = parser.parse_args()
    {"prepare": prepare, "build": build, "package": package}[args.stage]()
