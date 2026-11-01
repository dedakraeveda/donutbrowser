//! Bundled CBrowser engine integration.
//!
//! The portable runtime lives under `.local/cbrowser`. A machine-local override
//! may still be selected explicitly or supplied through `BROWSER_BINARY_PATH`.

use crate::browser::{create_browser, BrowserType, ProxySettings};
use crate::profile::BrowserProfile;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::time::Duration;
use sysinfo::{Pid, ProcessRefreshKind, RefreshKind};

#[path = "cbrowser_geo.rs"]
mod geo_supervisor;

/// Coordinates depend on the live CDP owner; close its browsers on app exit.
pub async fn shutdown_geo_browsers() {
  geo_supervisor::shutdown().await;
}

pub const EXTERNAL_VERSION: &str = "external";
pub const CBROWSER_RELEASE: &str = "1.33";
pub const DEFAULT_BUNDLED_VERSION: &str = "1.33";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CloakEngineStatus {
  pub available: bool,
  pub path: Option<String>,
  pub source: Option<String>,
  pub version: String,
  pub bundled: bool,
  pub release: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CloakRuntime {
  pid: u32,
  cdp_port: u16,
}

#[derive(Debug, Clone)]
pub struct CloakLaunchResult {
  pub process_id: u32,
  pub cdp_port: u16,
}

fn runtime_path(profile_path: &Path) -> PathBuf {
  profile_path
    .parent()
    .unwrap_or(profile_path)
    .join("cloak-runtime.json")
}

fn candidate_is_executable(path: &Path) -> bool {
  if !path.is_file()
    || !path.file_name().is_some_and(|candidate| {
      let candidate = candidate.to_string_lossy();
      executable_names()
        .iter()
        .any(|expected| candidate.eq_ignore_ascii_case(expected))
    })
  {
    return false;
  }
  #[cfg(target_os = "windows")]
  {
    use std::io::Read;
    let mut magic = [0u8; 2];
    let valid_pe = std::fs::File::open(path)
      .and_then(|mut file| file.read_exact(&mut magic))
      .is_ok()
      && magic == *b"MZ";
    let has_dll = path.parent().is_some_and(|dir| {
      std::fs::read_dir(dir).is_ok_and(|entries| {
        entries.flatten().any(|entry| {
          entry
            .path()
            .extension()
            .is_some_and(|ext| ext.eq_ignore_ascii_case("dll"))
        })
      })
    });
    valid_pe && has_dll
  }
  #[cfg(unix)]
  {
    use std::os::unix::fs::PermissionsExt;
    std::fs::metadata(path).is_ok_and(|metadata| metadata.permissions().mode() & 0o111 != 0)
  }
}

fn configured_path() -> Option<PathBuf> {
  crate::settings_manager::SettingsManager::instance()
    .load_settings()
    .ok()
    .and_then(|settings| settings.cloak_binary_path)
    .map(PathBuf::from)
    .filter(|path| candidate_is_executable(path))
}

fn cache_roots() -> Vec<PathBuf> {
  let mut roots = Vec::new();
  if let Ok(cache) = std::env::var("BROWSER_CACHE_DIR") {
    roots.push(PathBuf::from(cache));
  }
  let bundled = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
    .parent()
    .map(|root| root.join(".local").join("cbrowser").join("cache"));
  if let Some(bundled) = bundled {
    if !roots.contains(&bundled) {
      roots.push(bundled);
    }
  }
  roots
}

fn executable_names() -> &'static [&'static str] {
  #[cfg(target_os = "windows")]
  {
    &["chrome.exe", "chromium.exe"]
  }
  #[cfg(target_os = "macos")]
  {
    &["Chromium", "Google Chrome for Testing", "chrome"]
  }
  #[cfg(target_os = "linux")]
  {
    &["chrome", "chromium"]
  }
}

fn find_executable_under(root: &Path) -> Option<PathBuf> {
  if !root.is_dir() {
    return None;
  }
  let mut stack = vec![(root.to_path_buf(), 0usize)];
  let mut matches = Vec::new();
  while let Some((dir, depth)) = stack.pop() {
    if depth > 6 {
      continue;
    }
    let Ok(entries) = std::fs::read_dir(dir) else {
      continue;
    };
    for entry in entries.flatten() {
      let path = entry.path();
      if path.is_dir() {
        stack.push((path, depth + 1));
      } else if executable_names().iter().any(|name| {
        path
          .file_name()
          .is_some_and(|candidate| candidate.eq_ignore_ascii_case(name))
      }) && candidate_is_executable(&path)
      {
        matches.push(path);
      }
    }
  }
  matches.sort();
  matches.pop()
}

pub fn resolve_binary_path() -> Option<(PathBuf, &'static str)> {
  if let Some(path) = std::env::var_os("BROWSER_BINARY_PATH")
    .map(PathBuf::from)
    .filter(|path| candidate_is_executable(path))
  {
    return Some((path, "environment"));
  }
  if let Some(path) = configured_path() {
    return Some((path, "settings"));
  }
  let environment_version = std::env::var("BROWSER_VERSION").ok();
  cache_roots().into_iter().find_map(|root| {
    let selected_version = environment_version.clone().or_else(|| {
      std::fs::read_to_string(root.join(".selected-version"))
        .ok()
        .map(|version| version.trim().to_string())
        .filter(|version| !version.is_empty())
    });
    let version = selected_version.unwrap_or_else(|| DEFAULT_BUNDLED_VERSION.to_string());
    // Fork release labels are separate from Chromium's cache/protocol version.
    let version = if version == CBROWSER_RELEASE {
      include_str!("../../146_Cl.txt")
        .lines()
        .next()
        .unwrap_or("")
    } else {
      &version
    };
    let version_root = root.join(format!("chromium-{version}"));
    find_executable_under(&version_root).map(|path| (path, "cbrowser-cache"))
  })
}

pub fn is_available() -> bool {
  resolve_binary_path().is_some()
}

#[tauri::command]
pub fn get_cloak_engine_status() -> CloakEngineStatus {
  let resolved = resolve_binary_path();
  CloakEngineStatus {
    release: CBROWSER_RELEASE.to_string(),
    available: resolved.is_some(),
    path: resolved
      .as_ref()
      .map(|(path, _)| path.to_string_lossy().to_string()),
    source: resolved.as_ref().map(|(_, source)| source.to_string()),
    version: EXTERNAL_VERSION.to_string(),
    bundled: resolved
      .as_ref()
      .is_some_and(|(_, source)| *source == "cbrowser-cache"),
  }
}

#[tauri::command]
pub fn set_cloak_binary_path(path: Option<String>) -> Result<CloakEngineStatus, String> {
  let normalized = match path {
    Some(raw) if !raw.trim().is_empty() => {
      let candidate = PathBuf::from(raw.trim());
      if !candidate_is_executable(&candidate) {
        return Err(crate::backend_error_with_detail(
          "CLOAK_BINARY_INVALID",
          candidate.display(),
        ));
      }
      Some(candidate.to_string_lossy().to_string())
    }
    _ => None,
  };

  let manager = crate::settings_manager::SettingsManager::instance();
  let mut settings = manager
    .load_settings()
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?;
  settings.cloak_binary_path = normalized;
  manager
    .save_settings(&settings)
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?;
  Ok(get_cloak_engine_status())
}

fn fingerprint_seed(profile: &BrowserProfile) -> u64 {
  let bytes = profile.id.as_bytes();
  let raw = u64::from_be_bytes(bytes[..8].try_into().expect("UUID has sixteen bytes"));
  10_000 + raw % 90_000
}

async fn reserve_port() -> Result<u16, String> {
  let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
    .await
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?;
  let port = listener
    .local_addr()
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?
    .port();
  drop(listener);
  Ok(port)
}

fn process_is_running(pid: u32) -> bool {
  let system = crate::proxy_storage::process_table(
    RefreshKind::nothing().with_processes(ProcessRefreshKind::everything()),
  );
  system.process(Pid::from(pid as usize)).is_some()
}

fn process_matches_profile(process: &sysinfo::Process, profile_path: &str) -> bool {
  if process.cmd().iter().any(|arg| {
    let arg = arg.to_string_lossy();
    arg == profile_path || arg.strip_prefix("--user-data-dir=") == Some(profile_path)
  }) {
    return true;
  }
  #[cfg(target_os = "linux")]
  {
    // Some Chromium builds setproctitle() their argv into one flat string.
    // A substring alone is ambiguous (profile prefixes and paths with spaces):
    // require the exact profile's Chromium lock PID AND selected executable.
    let flattened = process.cmd().len() == 1
      && process.cmd()[0]
        .to_string_lossy()
        .contains(&format!("--user-data-dir={profile_path}"));
    if flattened && singleton_lock_pid(Path::new(profile_path)) == Some(process.pid().as_u32()) {
      let expected = resolve_binary_path().and_then(|(path, _)| path.canonicalize().ok());
      let actual = process.exe().and_then(|path| path.canonicalize().ok());
      return expected.is_some() && expected == actual;
    }
  }
  false
}

#[cfg(target_os = "linux")]
fn singleton_lock_pid(profile_path: &Path) -> Option<u32> {
  let target = std::fs::read_link(profile_path.join("SingletonLock")).ok()?;
  let name = target.file_name()?.to_str()?;
  let (host, pid) = name.rsplit_once('-')?;
  if host.is_empty() {
    return None;
  }
  pid.parse::<u32>().ok().filter(|pid| *pid > 0)
}

fn is_browser_root(process: &sysinfo::Process) -> bool {
  !process
    .cmd()
    .iter()
    .any(|arg| arg.to_string_lossy().starts_with("--type="))
}

fn discover_pid(profile_path: &str) -> Option<u32> {
  let system = crate::proxy_storage::process_table(
    RefreshKind::nothing().with_processes(ProcessRefreshKind::everything()),
  );
  let mut fallback = None;
  for (pid, process) in system
    .processes()
    .iter()
    .filter(|(_, process)| process_matches_profile(process, profile_path))
  {
    fallback.get_or_insert(pid.as_u32());
    if is_browser_root(process) {
      return Some(pid.as_u32());
    }
  }
  fallback
}

fn load_runtime(profile_path: &Path) -> Option<CloakRuntime> {
  let content = std::fs::read_to_string(runtime_path(profile_path)).ok()?;
  serde_json::from_str(&content).ok()
}

fn save_runtime(profile_path: &Path, runtime: &CloakRuntime) -> Result<(), String> {
  let content = serde_json::to_vec_pretty(runtime)
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?;
  std::fs::write(runtime_path(profile_path), content)
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))
}

fn remove_runtime(profile_path: &Path) {
  let _ = std::fs::remove_file(runtime_path(profile_path));
}

async fn wait_for_cdp(port: u16) -> Result<(), String> {
  let endpoint = format!("http://127.0.0.1:{port}/json/version");
  let client = reqwest::Client::new();
  let mut last_error = String::new();
  for _ in 0..40 {
    match client
      .get(&endpoint)
      .timeout(Duration::from_millis(750))
      .send()
      .await
    {
      Ok(response) if response.status().is_success() => return Ok(()),
      Ok(response) => last_error = format!("HTTP {}", response.status()),
      Err(error) => last_error = error.to_string(),
    }
    tokio::time::sleep(Duration::from_millis(250)).await;
  }
  Err(crate::backend_error_with_detail(
    "CLOAK_CDP_UNAVAILABLE",
    last_error,
  ))
}

fn geo_launch_args(
  geo: &crate::geolocation::Geolocation,
  seed: u64,
) -> Result<Vec<String>, String> {
  geo
    .timezone
    .parse::<chrono_tz::Tz>()
    .map_err(|_| crate::backend_error("CLOAK_LAUNCH_FAILED"))?;
  let region = geo
    .locale
    .region
    .as_deref()
    .ok_or_else(|| crate::backend_error("CLOAK_LAUNCH_FAILED"))?;
  let locale = crate::geolocation::locale_selector()
    .ok_or_else(|| crate::backend_error("CLOAK_LAUNCH_FAILED"))?
    .locale_for_seed(region, seed)
    .map_err(|_| crate::backend_error("CLOAK_LAUNCH_FAILED"))?
    .as_string();
  Ok(vec![
    format!("--fingerprint-timezone={}", geo.timezone),
    format!("--lang={locale}"),
    format!("--fingerprint-locale={locale}"),
  ])
}

#[cfg(test)]
async fn resolve_geo_args(proxy: Option<&ProxySettings>, seed: u64) -> Result<Vec<String>, String> {
  resolve_geo(proxy, seed).await.map(|(args, _)| args)
}

async fn resolve_geo(
  proxy: Option<&ProxySettings>,
  seed: u64,
) -> Result<(Vec<String>, crate::geolocation::Geolocation), String> {
  // Donut supplies its actual local routing worker. Never probe a direct exit
  // as fallback for a failed proxy; do not log proxy credentials or public IPs.
  let proxy = proxy.ok_or_else(|| crate::backend_error("EXIT_PROBE_FAILED"))?;
  if !matches!(
    proxy.proxy_type.to_lowercase().as_str(),
    "http" | "https" | "socks4" | "socks5"
  ) {
    return Err(crate::backend_error("EXIT_PROBE_FAILED"));
  }
  let url = crate::proxy_manager::ProxyManager::build_probe_proxy_url(proxy);
  let ip = tokio::time::timeout(
    Duration::from_secs(15),
    crate::ip_utils::fetch_public_ip(Some(&url)),
  )
  .await
  .map_err(|_| crate::backend_error("EXIT_PROBE_FAILED"))?
  .map_err(|_| crate::backend_error("EXIT_PROBE_FAILED"))?;
  let geo = crate::geolocation::get_geolocation(&ip).map_err(|_| {
    crate::backend_error_with_detail(
      "CLOAK_LAUNCH_FAILED",
      "GeoIP lookup unavailable; browser was not started",
    )
  })?;
  let mut args = geo_launch_args(&geo, seed)?;
  args.extend(webrtc_launch_args(&ip)?);
  Ok((args, geo))
}

fn webrtc_launch_args(exit_ip: &str) -> Result<Vec<String>, String> {
  let ip: std::net::IpAddr = exit_ip
    .parse()
    .map_err(|_| crate::backend_error("EXIT_PROBE_FAILED"))?;
  if ip.is_loopback() || ip.is_unspecified() || ip.is_multicast() {
    return Err(crate::backend_error("EXIT_PROBE_FAILED"));
  }
  Ok(vec![
    format!("--fingerprint-webrtc-ip={ip}"),
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp".to_string(),
  ])
}

pub async fn launch(
  profile: &BrowserProfile,
  profile_path: &Path,
  proxy: Option<&ProxySettings>,
  url: Option<&str>,
  extension_paths: &[String],
  remote_debugging_port: Option<u16>,
  headless: bool,
) -> Result<CloakLaunchResult, String> {
  let (executable, _) =
    resolve_binary_path().ok_or_else(|| crate::backend_error("CLOAK_BINARY_NOT_CONFIGURED"))?;
  std::fs::create_dir_all(profile_path)
    .map_err(|e| crate::backend_error_with_detail("INTERNAL_ERROR", e))?;
  let port = match remote_debugging_port {
    Some(port) => port,
    None => reserve_port().await?,
  };

  let browser = create_browser(BrowserType::Cloak);
  let mut args = browser
    .create_launch_args(
      &profile_path.to_string_lossy(),
      proxy,
      Some("about:blank".to_string()),
      Some(port),
      headless,
    )
    .map_err(|e| crate::backend_error_with_detail("CLOAK_LAUNCH_FAILED", e))?;
  let seed = fingerprint_seed(profile);
  args.push(format!("--fingerprint={seed}"));
  // Match the native Mac GPU/UA rather than applying the engine's Windows default.
  #[cfg(target_os = "macos")]
  args.push("--fingerprint-platform=macos".to_string());
  let (geo_args, geo) = resolve_geo(proxy, seed).await?;
  args.extend(geo_args);
  if !extension_paths.is_empty() {
    let joined = extension_paths.join(",");
    args.push(format!("--disable-extensions-except={joined}"));
    args.push(format!("--load-extension={joined}"));
  }

  #[cfg(target_os = "windows")]
  let child = crate::platform_browser::windows::launch_browser_process(&executable, &args).await;
  #[cfg(target_os = "macos")]
  let child = crate::platform_browser::macos::launch_browser_process(&executable, &args).await;
  #[cfg(target_os = "linux")]
  let child = crate::platform_browser::linux::launch_browser_process(&executable, &args).await;

  let child = child.map_err(|e| crate::backend_error_with_detail("CLOAK_LAUNCH_FAILED", e))?;
  let launcher_pid = child.id();
  if let Err(error) = wait_for_cdp(port).await {
    let _ = stop_pid(launcher_pid, profile_path).await;
    return Err(error);
  }
  if let Err(reason) = geo_supervisor::supervise(
    port,
    geo.latitude,
    geo.longitude,
    profile_path.to_path_buf(),
  )
  .await
  {
    let _ = stop_pid(launcher_pid, profile_path).await;
    // The supervisor only returns fixed stage labels, never raw CDP/page data.
    return Err(crate::backend_error_with_detail(
      "CLOAK_LAUNCH_FAILED",
      reason,
    ));
  }
  let profile_path_string = profile_path.to_string_lossy();
  let process_id = if process_is_running(launcher_pid) {
    launcher_pid
  } else {
    discover_pid(&profile_path_string).unwrap_or(launcher_pid)
  };
  save_runtime(
    profile_path,
    &CloakRuntime {
      pid: process_id,
      cdp_port: port,
    },
  )?;
  if let Some(url) = url {
    if let Err(error) = open_url(profile_path, url).await {
      let _ = stop_pid(process_id, profile_path).await;
      remove_runtime(profile_path);
      return Err(error);
    }
  }
  Ok(CloakLaunchResult {
    process_id,
    cdp_port: port,
  })
}

pub fn get_cdp_port(profile_path: &Path) -> Option<u16> {
  let runtime = load_runtime(profile_path)?;
  if process_is_running(runtime.pid) {
    Some(runtime.cdp_port)
  } else {
    remove_runtime(profile_path);
    None
  }
}

pub fn find_process(profile_path: &Path) -> Option<u32> {
  if let Some(runtime) = load_runtime(profile_path) {
    if process_is_running(runtime.pid) {
      return Some(runtime.pid);
    }
  }
  let profile_path_string = profile_path.to_string_lossy();
  discover_pid(&profile_path_string)
}

async fn stop_pid(pid: u32, _profile_path: &Path) -> Result<(), String> {
  #[cfg(target_os = "windows")]
  let result = crate::platform_browser::windows::kill_browser_process_impl(pid).await;
  #[cfg(target_os = "macos")]
  let result = crate::platform_browser::macos::kill_browser_process_impl(
    pid,
    Some(&_profile_path.to_string_lossy()),
  )
  .await;
  #[cfg(target_os = "linux")]
  let result = crate::platform_browser::linux::kill_browser_process_impl(
    pid,
    Some(&_profile_path.to_string_lossy()),
  )
  .await;
  result.map_err(|e| crate::backend_error_with_detail("CLOAK_STOP_FAILED", e))
}

pub async fn stop(profile_path: &Path, fallback_pid: Option<u32>) -> Result<(), String> {
  let pid = find_process(profile_path).or(fallback_pid);
  if let Some(pid) = pid {
    stop_pid(pid, profile_path).await?;
  }
  remove_runtime(profile_path);
  Ok(())
}

pub async fn open_url(profile_path: &Path, url: &str) -> Result<(), String> {
  let port =
    get_cdp_port(profile_path).ok_or_else(|| crate::backend_error("CLOAK_CDP_UNAVAILABLE"))?;
  let endpoint = format!(
    "http://127.0.0.1:{port}/json/new?{}",
    urlencoding::encode(url)
  );
  let response = reqwest::Client::new()
    .put(endpoint)
    .timeout(Duration::from_secs(5))
    .send()
    .await
    .map_err(|e| crate::backend_error_with_detail("CLOAK_CDP_UNAVAILABLE", e))?;
  if response.status().is_success() {
    Ok(())
  } else {
    Err(crate::backend_error_with_detail(
      "CLOAK_CDP_UNAVAILABLE",
      response.status(),
    ))
  }
}

#[cfg(test)]
mod tests {
  use super::*;

  #[cfg(target_os = "linux")]
  #[test]
  fn singleton_pid_requires_exact_profile_symlink_not_plaintext_or_prefix() {
    use std::os::unix::fs::symlink;
    let temp = tempfile::tempdir().unwrap();
    let profile = temp.path().join("profile with spaces");
    std::fs::create_dir(&profile).unwrap();
    assert_eq!(singleton_lock_pid(&profile), None);
    std::fs::write(profile.join("SingletonLock"), "host-123").unwrap();
    assert_eq!(singleton_lock_pid(&profile), None);
    std::fs::remove_file(profile.join("SingletonLock")).unwrap();
    symlink("test-host-123", profile.join("SingletonLock")).unwrap();
    assert_eq!(singleton_lock_pid(&profile), Some(123));
    assert_eq!(singleton_lock_pid(temp.path()), None);
    std::fs::remove_file(profile.join("SingletonLock")).unwrap();
    symlink("test-host-0", profile.join("SingletonLock")).unwrap();
    assert_eq!(singleton_lock_pid(&profile), None);
  }

  #[test]
  fn fingerprint_seed_is_stable_and_in_documented_range() {
    let profile = BrowserProfile {
      id: uuid::Uuid::parse_str("12345678-1234-1234-1234-123456789abc").unwrap(),
      ..Default::default()
    };
    let first = fingerprint_seed(&profile);
    assert_eq!(first, fingerprint_seed(&profile));
    assert!((10_000..100_000).contains(&first));
  }

  #[test]
  fn geo_flags_are_stable_and_use_the_exit_timezone() {
    let geo = crate::geolocation::Geolocation {
      locale: crate::geolocation::Locale {
        language: "fi".into(),
        region: Some("FI".into()),
      },
      timezone: "Europe/Helsinki".into(),
      latitude: 60.0,
      longitude: 25.0,
    };
    let first = geo_launch_args(&geo, 47123).unwrap();
    assert_eq!(first, geo_launch_args(&geo, 47123).unwrap());
    assert_eq!(first[0], "--fingerprint-timezone=Europe/Helsinki");
    assert_eq!(
      first[1].strip_prefix("--lang="),
      first[2].strip_prefix("--fingerprint-locale=")
    );
    let mut changed = geo.clone();
    changed.timezone = "invalid/timezone".into();
    assert!(geo_launch_args(&changed, 47123).is_err());
    changed = geo;
    changed.locale.region = None;
    assert!(geo_launch_args(&changed, 47123).is_err());
  }

  #[tokio::test]
  async fn geo_probe_never_falls_back_without_supported_proxy() {
    assert!(resolve_geo_args(None, 47123).await.is_err());
    let proxy = ProxySettings {
      proxy_type: "unsupported".into(),
      host: "127.0.0.1".into(),
      port: 1,
      username: None,
      password: None,
      vless_uri: None,
    };
    assert!(resolve_geo_args(Some(&proxy), 47123).await.is_err());
  }

  #[test]
  fn locale_seed_selection_is_stable_and_country_scoped() {
    let selector = crate::geolocation::LocaleSelector::new().unwrap();
    for seed in [0, 1, 10000, 47123, u64::MAX] {
      for country in ["FI", "US", "DE"] {
        let a = selector.locale_for_seed(country, seed).unwrap();
        assert_eq!(
          a.as_string(),
          selector.locale_for_seed(country, seed).unwrap().as_string()
        );
        assert_eq!(a.region.as_deref(), Some(country));
        assert_eq!(selector.region_speaks(country, &a.language), Some(true));
      }
    }
    assert!(selector.locale_for_seed("INVALID", 1).is_err());
  }

  #[tokio::test]
  #[ignore = "Owner-requested live proxy/MaxMind check; requires CBROWSER_TEST_PROXY_PORT"]
  async fn live_geo_resolver_through_approved_loopback_proxy() {
    let port: u16 = std::env::var("CBROWSER_TEST_PROXY_PORT")
      .unwrap()
      .parse()
      .unwrap();
    assert!(port > 1024);
    let proxy = ProxySettings {
      proxy_type: "http".into(),
      host: "127.0.0.1".into(),
      port,
      username: None,
      password: None,
      vless_uri: None,
    };
    let args = resolve_geo_args(Some(&proxy), 47123).await.unwrap();
    assert_eq!(args.len(), 5);
    println!("Resolved geo and WebRTC flags; IP withheld");
    assert_eq!(args, resolve_geo_args(Some(&proxy), 47123).await.unwrap());
  }

  #[test]
  fn webrtc_flags_validate_ip_and_disable_direct_udp() {
    let args = webrtc_launch_args("203.0.113.9").unwrap();
    assert_eq!(args[0], "--fingerprint-webrtc-ip=203.0.113.9");
    assert_eq!(
      args[1],
      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"
    );
    for invalid in ["auto", "127.0.0.1", "::", "224.0.0.1", "1.2.3.4 --flag"] {
      assert!(webrtc_launch_args(invalid).is_err());
    }
  }

  #[test]
  fn invalid_configured_binary_is_not_reported_available() {
    assert!(!candidate_is_executable(Path::new(
      "this/path/does/not/exist"
    )));
  }
}
