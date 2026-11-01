fn main() {
    #[cfg(target_os = "windows")]
    {
        let manifest_dir = std::path::PathBuf::from(
            std::env::var("CARGO_MANIFEST_DIR").expect("Cargo must provide CARGO_MANIFEST_DIR"),
        );
        let manifest = manifest_dir
            .join("..")
            .join("..")
            .join("src-tauri")
            .join("app.manifest");
        let manifest = manifest.to_string_lossy().replace('/', "\\");

        println!("cargo:rustc-link-arg=/MANIFEST:EMBED");
        println!("cargo:rustc-link-arg=/MANIFESTINPUT:{manifest}");
        println!("cargo:rerun-if-changed=../../src-tauri/app.manifest");
    }
}
