"""Agent CLI Runner for Donut CBrowser 1.33 (technical build in root 146_Cl.txt).

Adheres to AGENT_CLI_CONTRACT:
capabilities -> status -> preflight -> plan -> apply -> verify
Runs headless automation on loopback CDP using isolated profiles on drive D:.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from typing import Any, Dict, List, Optional

CONTRACT_VERSION = 1
LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
TOKEN_PATH = LOCAL_APPDATA / "Quite" / "PiAuthBrowser" / "donut-api.dpapi"
SETTINGS_PATH = LOCAL_APPDATA / "DonutBrowser" / "settings" / "app_settings.json"


def protect(data: bytes, decrypt: bool = False) -> bytes:
    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(Blob),
    ]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError("DPAPI unprotect failed")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def get_api_config() -> tuple[int, str]:
    if not SETTINGS_PATH.is_file():
        raise FileNotFoundError(f"Donut settings not found at {SETTINGS_PATH}")
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
    port = settings.get("api_port")
    if settings.get("api_enabled") is not True or type(port) is not int:
        raise RuntimeError("Donut Local REST API is disabled in app settings")
    if not TOKEN_PATH.is_file():
        raise FileNotFoundError(f"Donut API token not found at {TOKEN_PATH}")
    token = protect(TOKEN_PATH.read_bytes(), decrypt=True).decode("utf-8")
    return port, token


def api_call(method: str, path: str, payload: Optional[dict] = None, timeout: float = 30.0) -> Any:
    port, token = get_api_config()
    url = f"http://127.0.0.1:{port}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        return json.loads(body.decode("utf-8")) if body else {}


def get_capabilities() -> Dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "commands": ["capabilities", "status", "preflight", "plan", "apply", "verify"],
        "modes": ["open-url", "run-profile", "kill-profile"],
        "engine": "CBrowser 1.33",
        "isolation": "user-data isolated per profile on drive D:, no profile tampering",
        "description": "Agent CLI Runner for Donut CBrowser stealth profiles",
    }


def get_status() -> Dict[str, Any]:
    try:
        port, _ = get_api_config()
        profiles = api_call("GET", "/v1/profiles").get("profiles", [])
        cbrowser_profiles = [p for p in profiles if p.get("browser") == "cloak"]
        pi_tasks = [p for p in cbrowser_profiles if str(p.get("name", "")).startswith("Pi Tasks")]
        return {
            "contractVersion": CONTRACT_VERSION,
            "apiReachable": True,
            "apiPort": port,
            "totalProfiles": len(profiles),
            "cbrowserProfilesCount": len(cbrowser_profiles),
            "piTasksProfiles": [
                {"id": p.get("id"), "name": p.get("name"), "running": bool(p.get("process_id"))}
                for p in pi_tasks
            ],
            "defaultProfileId": pi_tasks[0]["id"] if pi_tasks else None,
        }
    except Exception as e:
        return {
            "contractVersion": CONTRACT_VERSION,
            "apiReachable": False,
            "error": str(e),
        }


def plan_action(url: str, profile_id: Optional[str] = None) -> Dict[str, Any]:
    status_data = get_status()
    if not status_data.get("apiReachable"):
        raise RuntimeError(f"Donut API not reachable: {status_data.get('error')}")

    pid = profile_id or status_data.get("defaultProfileId")
    if not pid:
        raise ValueError("No valid CBrowser profile found")

    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"Invalid URL: {url}")

    plan_payload = {
        "profileId": pid,
        "action": "open-url",
        "url": url,
    }
    digest = hashlib.sha256(json.dumps(plan_payload, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "contractVersion": CONTRACT_VERSION,
        "action": "open-url",
        "planPayload": plan_payload,
        "digest": digest,
        "targetUrl": url,
        "profileId": pid,
    }


def apply_action(plan: Dict[str, Any]) -> Dict[str, Any]:
    payload = plan.get("planPayload") or plan
    pid = payload["profileId"]
    url = payload["url"]

    # Open URL via Donut REST
    res = api_call("POST", f"/v1/profiles/{pid}/open-url", {"url": url})
    return {
        "contractVersion": CONTRACT_VERSION,
        "action": "open-url",
        "profileId": pid,
        "url": url,
        "result": res,
        "executedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main():
    parser = argparse.ArgumentParser(description="Donut CBrowser Agent Runner")
    parser.add_argument("operation", choices=["capabilities", "status", "preflight", "plan", "apply", "verify"])
    parser.add_argument("--url", help="Target URL to navigate")
    parser.add_argument("--profile-id", help="Profile UUID (default: first Pi Tasks profile)")
    parser.add_argument("--plan-json", help="Path to plan JSON file for apply")

    args = parser.parse_args()

    try:
        if args.operation == "capabilities":
            res = get_capabilities()
        elif args.operation == "status":
            res = get_status()
        elif args.operation in ("preflight", "plan"):
            if not args.url:
                raise ValueError("--url is required for preflight and plan")
            res = plan_action(args.url, args.profile_id)
        elif args.operation == "apply":
            if args.plan_json:
                plan_data = json.loads(Path(args.plan_json).read_text(encoding="utf-8"))
            elif args.url:
                plan_data = plan_action(args.url, args.profile_id)
            else:
                raise ValueError("Either --plan-json or --url is required for apply")
            res = apply_action(plan_data)
        elif args.operation == "verify":
            res = get_status()
        else:
            raise ValueError(f"Unknown operation: {args.operation}")

        print(json.dumps({"ok": True, "operation": args.operation, "result": res}, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"ok": False, "operation": args.operation, "error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
