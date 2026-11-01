use crate::cloud_auth::CLOUD_AUTH;

/// Local-only capabilities are enabled by default in this authorized fork.
/// Set DONUT_LOCAL_FEATURES=0/false/off/no to build or run it with upstream
/// subscription gates. This never grants access to Donut-hosted services.
const LOCAL_FEATURES_DEFAULT_ENABLED: bool = true;

/// Executable code in authorized builds is updated only through the reviewed
/// agent runbook. This is deliberately not configurable at runtime: an
/// environment variable or copied upstream setting must never re-enable app or
/// browser-binary replacement. Signed, non-executable data has a separate
/// policy and may refresh with last-known-good rollback.
const MANUAL_EXECUTABLE_UPDATES_ONLY: bool = true;
const MANUAL_EXTERNAL_DATA_UPDATES_ONLY: bool = false;

pub struct EntitlementsPolicy;

impl EntitlementsPolicy {
  pub fn local_features_enabled() -> bool {
    local_features_enabled_with_override(std::env::var("DONUT_LOCAL_FEATURES").ok().as_deref())
  }

  pub const fn agent_managed_updates_only() -> bool {
    MANUAL_EXECUTABLE_UPDATES_ONLY
  }

  pub const fn manual_app_updates_only() -> bool {
    MANUAL_EXECUTABLE_UPDATES_ONLY
  }

  pub const fn manual_browser_updates_only() -> bool {
    MANUAL_EXECUTABLE_UPDATES_ONLY
  }

  pub const fn manual_external_data_updates_only() -> bool {
    MANUAL_EXTERNAL_DATA_UPDATES_ONLY
  }

  /// Guard for app, Wayfern, CBrowser, and other executable downloads.
  pub fn update_downloads_blocked() -> bool {
    if !Self::manual_browser_updates_only() {
      return false;
    }
    #[cfg(feature = "e2e")]
    if crate::e2e_automation_enabled()
      && std::env::var("DONUT_E2E_ALLOW_UPDATE_DOWNLOADS").as_deref() == Ok("1")
    {
      return false;
    }
    true
  }

  /// Data files cannot execute and are replaced with validation and rollback.
  pub const fn external_data_downloads_blocked() -> bool {
    Self::manual_external_data_updates_only()
  }

  /// Launch and drive browsers through the loopback REST API or MCP server.
  pub async fn can_use_browser_automation() -> bool {
    Self::local_features_enabled() || CLOUD_AUTH.can_use_browser_automation().await
  }

  /// View and edit locally stored fingerprint configuration.
  pub async fn can_edit_fingerprints() -> bool {
    Self::local_features_enabled() || CLOUD_AUTH.can_use_cross_os_fingerprints().await
  }

  /// Select a fingerprint OS other than the host OS. Wayfern still requires a
  /// valid token for applying a cross-OS identity; DONUT_WAYFERN_TOKEN provides
  /// an authorized externally issued token without requiring Donut cloud login.
  pub async fn can_use_cross_os_fingerprints() -> bool {
    Self::local_features_enabled() || CLOUD_AUTH.can_use_cross_os_fingerprints().await
  }

  pub async fn is_fingerprint_os_allowed(fingerprint_os: Option<&str>) -> bool {
    let host_os = crate::profile::types::get_host_os();
    match fingerprint_os {
      None => true,
      Some(os) if os == host_os => true,
      Some(_) => Self::can_use_cross_os_fingerprints().await,
    }
  }

  /// Extension files and groups are local entities. Cloud sync of those files
  /// remains governed by the selected sync backend.
  pub async fn can_manage_extensions() -> bool {
    Self::local_features_enabled() || CLOUD_AUTH.has_active_paid_subscription().await
  }

  /// Cloud-backed capabilities intentionally do not inherit local access.
  pub async fn can_use_cookie_bot() -> bool {
    CLOUD_AUTH.can_use_cookie_bot().await
  }

  pub async fn can_use_remote_automation() -> bool {
    CLOUD_AUTH.can_use_browser_automation().await
  }

  pub async fn is_on_team_plan() -> bool {
    CLOUD_AUTH.is_on_team_plan().await
  }
}

pub fn external_wayfern_token() -> Option<String> {
  std::env::var("DONUT_WAYFERN_TOKEN")
    .ok()
    .map(|token| token.trim().to_string())
    .filter(|token| !token.is_empty())
}

fn local_features_enabled_with_override(value: Option<&str>) -> bool {
  value
    .and_then(parse_bool_override)
    .unwrap_or(LOCAL_FEATURES_DEFAULT_ENABLED)
}

fn parse_bool_override(value: &str) -> Option<bool> {
  match value.trim().to_ascii_lowercase().as_str() {
    "1" | "true" | "yes" | "on" => Some(true),
    "0" | "false" | "no" | "off" => Some(false),
    _ => None,
  }
}

#[cfg(test)]
mod tests {
  use super::*;

  #[test]
  fn parses_local_feature_override() {
    for value in ["1", "true", "YES", "on"] {
      assert_eq!(parse_bool_override(value), Some(true));
    }
    for value in ["0", "false", "NO", "off"] {
      assert_eq!(parse_bool_override(value), Some(false));
    }
    assert_eq!(parse_bool_override("unexpected"), None);
  }

  #[test]
  fn authorized_fork_defaults_to_local_features_without_override() {
    assert!(local_features_enabled_with_override(None));
    assert!(!local_features_enabled_with_override(Some("false")));
  }

  #[test]
  fn authorized_fork_separates_executable_and_data_update_policy() {
    assert!(EntitlementsPolicy::manual_app_updates_only());
    assert!(EntitlementsPolicy::manual_browser_updates_only());
    assert!(EntitlementsPolicy::update_downloads_blocked());
    assert!(!EntitlementsPolicy::manual_external_data_updates_only());
    assert!(!EntitlementsPolicy::external_data_downloads_blocked());
  }
}
