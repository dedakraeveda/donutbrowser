# Profile clone API candidate — not deployed

Owner authorized cloning My Profile into My Profile RU, with no proxy/VPN in the copy. Source manager already implements clone_profile, registered as a native Tauri UI command, but neither existing REST nor MCP exposed it.

Added source endpoint POST /v1/profiles/{id}/clone to api_server.rs and OpenAPI/router. Payload: name, confirm_copy_session=true, optional direct=true. It calls the existing manager clone (source process_id must be absent), rejects existing names, copies through Donut, and clears proxy_id/vpn_id/launch_hook/bypass only on the new profile when direct=true. Source metadata is not changed. Cloning is not idempotent: inspect profiles after uncertain response; no automatic retry. Partial file-copy failure recovery remains the upstream manager's responsibility. Direct route save is subsequent to clone, not atomic; an error must prohibit launch. Authenticated API only.

Status: rustfmt syntax/format completed. cargo test --lib api_server::tests:: failed before project compilation: link.exe absent. vswhere -all -products * found no installed VS toolchain. No build, installation, binary replacement, cloning or profile-data transfer took place. Functional/native E2E and full format/lint/unit suite are NOT verified. Do not treat source route as an installed feature.

Existing installed UI command can clone without a new build: stop source profile, open profile details/actions -> Clone profile -> new name My Profile RU, then remove inherited proxy/VPN BEFORE launching the clone. The previously created empty RU profile b0528231-fa37-424f-a112-e9a0401712e5 was renamed to 'RU — пустой резерв (не копия)' to free the intended name; not deleted.

Pre-edit api_server.rs backup: D:/projects/temp/donut-clone-api-backup/api_server.rs. Existing working tree contains many unrelated edits; never reset it. Rollback only this endpoint/schema/router/test additions or restore the backup only after confirming no subsequent edits.
