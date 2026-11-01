import Foundation
import CryptoKit
import AppKit

// Native macOS entrypoint. Tokens/passwords/OTP are never arguments or output.
struct KitFailure: Error { let code: String }
let root = Bundle.main.bundleURL.resolvingSymlinksInPath()
let resources = root.appendingPathComponent("Contents/Resources")
let app = root.appendingPathComponent("Contents/MacOS/donutbrowser-kit")
let fm = FileManager.default
let state = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("DonutAgentKit")

func fail(_ code: String) throws -> Never { throw KitFailure(code: code) }
func json(_ url: URL) throws -> [String: Any] {
    guard let value = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [String: Any] else { try fail("invalid-json") }
    return value
}
func manifest() throws -> [String: Any] { try json(resources.appendingPathComponent("MANIFEST.json")) }
func engine() throws -> URL? {
    let metadata = try json(resources.appendingPathComponent("KIT.json"))
    guard let relative = metadata["engineExecutable"] as? String else { return nil }
    let candidate = resources.appendingPathComponent(relative).resolvingSymlinksInPath()
    guard candidate.path.hasPrefix(resources.path + "/"), fm.isExecutableFile(atPath: candidate.path) else { try fail("native-macos-engine-missing") }
    return candidate
}
func integrity() throws -> Int {
    guard let files = try manifest()["files"] as? [String: String] else { try fail("manifest-invalid") }
    for (relative, expected) in files {
        let file = root.appendingPathComponent(relative).resolvingSymlinksInPath()
        guard file.path.hasPrefix(root.path + "/"), fm.fileExists(atPath: file.path) else { try fail("manifest-path-invalid") }
        let handle = try FileHandle(forReadingFrom: file)
        defer { try? handle.close() }
        var digest = SHA256()
        while let chunk = try handle.read(upToCount: 1048576), !chunk.isEmpty { digest.update(data: chunk) }
        let actual = digest.finalize().map { String(format: "%02x", $0) }.joined()
        guard actual == expected else { try fail("payload-hash-mismatch") }
    }
    return files.count
}
func running() -> [pid_t] {
    NSRunningApplication.runningApplications(withBundleIdentifier: "com.donutbrowser.agentkit").filter {
        $0.processIdentifier != ProcessInfo.processInfo.processIdentifier && $0.executableURL?.resolvingSymlinksInPath() == app
    }.map { $0.processIdentifier }
}
func preflight() throws -> URL {
    guard fm.isExecutableFile(atPath: app.path) else { try fail("native-manager-missing") }
    guard let browser = try engine() else { try fail("macos-engine-required") }
    return browser
}
func emit(_ value: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]),
       let text = String(data: data, encoding: .utf8) { print(text) }
}
func result(_ op: String, _ data: [String: Any]) -> [String: Any] {
    ["ok": true, "operation": op, "contractVersion": 1, "result": data,
     "evidence": ["verifiedAt": ISO8601DateFormatter().string(from: Date()), "scope": root.path, "status": "local-check"]]
}
func launch() throws -> [String: Any] {
    let browser = try preflight()
    let count = try integrity()
    let existing = running()
    if !existing.isEmpty { return ["alreadyRunning": true, "runningPids": existing, "liveMcpChecked": false] }
    let settings = state.appendingPathComponent("data/settings/app_settings.json")
    try fm.createDirectory(at: settings.deletingLastPathComponent(), withIntermediateDirectories: true)
    if !fm.fileExists(atPath: settings.path) {
        let defaults: [String: Any] = ["onboarding_completed": true, "disable_auto_updates": true, "cloak_binary_path": browser.path]
        try JSONSerialization.data(withJSONObject: defaults).write(to: settings, options: .withoutOverwriting)
        try fm.setAttributes([.posixPermissions: 0o600], ofItemAtPath: settings.path)
    }
    let temp = state.appendingPathComponent("tmp")
    try fm.createDirectory(at: temp, withIntermediateDirectories: true)
    var env = ProcessInfo.processInfo.environment.filter { !$0.key.hasPrefix("DONUT") && !$0.key.hasPrefix("BROWSER_") }
    env["DONUTBROWSER_DATA_ROOT"] = state.path
    env["BROWSER_BINARY_PATH"] = browser.path
    if let version = try json(resources.appendingPathComponent("KIT.json"))["engineTechnicalVersion"] as? String { env["BROWSER_VERSION"] = version }
    env["TMPDIR"] = temp.path; env["TMP"] = temp.path; env["TEMP"] = temp.path
    let process = Process()
    process.executableURL = app; process.currentDirectoryURL = app.deletingLastPathComponent(); process.environment = env
    process.standardInput = FileHandle.nullDevice
    // No inherited agent protocol handles; use only this kit's bounded state log.
    let logURL = state.appendingPathComponent("launcher.log")
    if !fm.fileExists(atPath: logURL.path) { fm.createFile(atPath: logURL.path, contents: nil, attributes: [.posixPermissions: 0o600]) }
    let log = try FileHandle(forWritingTo: logURL); try log.seekToEnd()
    process.standardOutput = log; process.standardError = log
    try process.run(); Thread.sleep(forTimeInterval: 3)
    guard process.isRunning else { try fail("manager-exited") }
    return ["pid": process.processIdentifier, "processAlive": true, "payloadFilesVerified": count, "cbrowserRelease": "1.33", "liveMcpChecked": false]
}
let args = Array(CommandLine.arguments.dropFirst())
let op = args.first ?? "launch"
do {
    guard args.count <= 2 && (args.count < 2 || args[1] == "--json") else { try fail("invalid-arguments") }
    var data: [String: Any]
    switch op {
    case "capabilities", "--help":
        data = ["commands": ["capabilities", "status", "preflight", "plan", "verify", "launch"], "cbrowserRelease": "1.33",
                "uiRequired": ["MCP/REST token setup", "Account login/OTP"], "noCredentialMigration": true]
    case "status": data = ["appPresent": fm.fileExists(atPath: app.path), "enginePresent": try engine() != nil,
                            "runningPids": running(), "cbrowserRelease": "1.33", "liveMcpChecked": false]
    case "verify": data = ["payloadFilesVerified": try integrity(), "enginePresent": try engine() != nil, "liveMcpChecked": false]
    case "preflight", "plan": data = ["browser": try preflight().path, "writes": [state.path], "changesInstalledDonut": false]
    case "launch": data = try launch()
    default: try fail("invalid-command")
    }
    emit(result(op, data))
} catch {
    let code = (error as? KitFailure)?.code ?? "internal-error"
    emit(["ok": false, "operation": op, "contractVersion": 1,
          "error": ["code": code, "stage": "preflight-or-verify", "retryable": false, "nextAction": "Read the included macOS guide; never send credentials to your agent"]])
    if args.isEmpty { let alert = NSAlert(); alert.messageText = "Donut Agent Kit"; alert.informativeText = code + "\nRead the included macOS guide."; alert.runModal() }
    exit(error is KitFailure ? 2 : 1)
}
