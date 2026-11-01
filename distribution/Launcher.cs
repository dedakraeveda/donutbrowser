using System;
using System.IO;
using System.Diagnostics;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Threading;
using System.Text;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using System.Windows.Forms;

// A bounded offline launcher, not a browser automation framework or secret store.
internal static class Launcher {
    static readonly string Root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
    static readonly string App = Path.Combine(Root, "app", "donutbrowser-kit.exe");
    static readonly string Engine = Path.Combine(Root, "cbrowser", "chrome.exe");
    static readonly string State = Path.Combine(Root, "state");
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = Int32.MaxValue };
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct Startup { public int cb; public string reserved, desktop, title; public int x,y,cx,cy,xChars,yChars,fill,flags; public short show,cbReserved; public IntPtr reserved2,input,output,error; }
    [StructLayout(LayoutKind.Sequential)]
    struct ProcessInfo { public IntPtr process,thread; public int pid,tid; }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool CreateProcessW(string application, StringBuilder command, IntPtr pa, IntPtr ta, bool inherit, uint flags, IntPtr environment, string cwd, ref Startup startup, out ProcessInfo info);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    static Process StartIsolated(ProcessStartInfo start) {
        // No inherited stdio handles: a GUI child must not keep an agent's JSON pipe open.
        var keys = new List<string>(); foreach (string key in start.EnvironmentVariables.Keys) keys.Add(key);
        keys.Sort(StringComparer.OrdinalIgnoreCase);
        var block = new StringBuilder(); foreach (string key in keys) block.Append(key).Append('=').Append(start.EnvironmentVariables[key]).Append('\0');
        block.Append('\0'); IntPtr memory = Marshal.StringToHGlobalUni(block.ToString());
        var startup = new Startup(); startup.cb = Marshal.SizeOf(typeof(Startup)); ProcessInfo info;
        try {
            if (!CreateProcessW(App,new StringBuilder("\""+App+"\""),IntPtr.Zero,IntPtr.Zero,false,0x08000400,memory,start.WorkingDirectory,ref startup,out info))
                throw new InvalidOperationException("manager-start-failed");
            CloseHandle(info.thread); CloseHandle(info.process); return Process.GetProcessById(info.pid);
        } finally { Marshal.FreeHGlobal(memory); }
    }
    static object Result(string op, object value) {
        return new { ok = true, operation = op, contractVersion = 1, result = value,
            evidence = new { verifiedAt = DateTime.UtcNow.ToString("o"), scope = Root, status = "local-check" } };
    }
    static int Emit(object value, int code) {
        string text = Json.Serialize(value);
        using (var writer = new StreamWriter(Console.OpenStandardOutput())) { writer.WriteLine(text); }
        return code;
    }
    static List<int> Running(bool rejectOther) {
        var ids = new List<int>();
        foreach (var p in Process.GetProcessesByName("donutbrowser-kit")) {
            try {
                string path = p.MainModule.FileName;
                if (String.Equals(Path.GetFullPath(path), App, StringComparison.OrdinalIgnoreCase)) ids.Add(p.Id);
                else if (rejectOther) throw new InvalidOperationException("another-kit-running");
            } catch (System.ComponentModel.Win32Exception) {
                if (rejectOther) throw new InvalidOperationException("kit-process-unverifiable");
            } finally { p.Dispose(); }
        }
        return ids;
    }
    static void Preflight() {
        if (!File.Exists(App) || !File.Exists(Engine) || !File.Exists(Path.Combine(Root, "MANIFEST.json")))
            throw new InvalidOperationException("payload-missing");
        if (new DriveInfo(Path.GetPathRoot(Root)).AvailableFreeSpace < 2L * 1024 * 1024 * 1024)
            throw new InvalidOperationException("destination-disk-low");
        if (String.Equals(Path.GetPathRoot(Root), "C:\\", StringComparison.OrdinalIgnoreCase) &&
            new DriveInfo("C:\\").AvailableFreeSpace < 20L * 1024 * 1024 * 1024)
            throw new InvalidOperationException("system-disk-low-use-another-drive");
        Running(true);
    }
    static int Integrity() {
        var manifest = Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(Path.Combine(Root, "MANIFEST.json")));
        var files = (Dictionary<string, object>)manifest["files"];
        foreach (var pair in files) {
            string path = Path.GetFullPath(Path.Combine(Root, pair.Key.Replace('/', Path.DirectorySeparatorChar)));
            if (!path.StartsWith(Root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
                throw new InvalidOperationException("manifest-path-invalid");
            string hash;
            using (var algo = SHA256.Create()) using (var stream = File.OpenRead(path))
                hash = BitConverter.ToString(algo.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
            if (!String.Equals(hash, (string)pair.Value, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("payload-hash-mismatch");
        }
        return files.Count;
    }
    [STAThread]
    static int Main(string[] args) {
        string op = args.Length == 0 ? "launch" : args[0].TrimStart('-');
        bool interactive = args.Length == 0;
        try {
            if (args.Length > 2 || (args.Length == 2 && args[1] != "--json")) throw new InvalidOperationException("invalid-arguments");
            if (op == "help" || op == "h")
                return Emit(Result(op, new { commands = "capabilities,status,preflight,plan,launch,verify; append --json for agent use", secrets = "Never pass tokens/passwords/OTP in arguments. Configure MCP locally in Donut UI." }), 0);
            if (op == "capabilities")
                return Emit(Result(op, new { commands = new [] { "capabilities", "status", "preflight", "plan", "launch", "verify" },
                    uiRequired = new [] { "MCP/REST enable and local token entry", "Account login/OTP", "Profile creation and proxy configuration" },
                    boundary = "Only this offline kit; no installed manager changes, no token/profile migration, no remote endpoints" }), 0);
            if (op == "status")
                return Emit(Result(op, new { appPresent = File.Exists(App), enginePresent = File.Exists(Engine), statePresent = Directory.Exists(State), cbrowserRelease = "1.33",
                    runningPids = Running(false), liveMcpChecked = false }), 0);
            if (op == "preflight" || op == "plan") {
                Preflight();
                return Emit(Result(op, new { ready = true, writes = new [] { State }, willLaunch = App, browser = Engine,
                    changesInstalledDonut = false, copiesPersonalProfiles = false, mcpSetup = "ui-required" }), 0);
            }
            if (op == "verify") {
                Preflight();
                int count = Integrity();
                return Emit(Result(op, new { payloadFilesVerified = count, runningPids = Running(true), liveMcpChecked = false }), 0);
            }
            if (op != "launch") throw new InvalidOperationException("invalid-command");
            Preflight();
            int verified = Integrity();
            var running = Running(true);
            if (running.Count > 0) {
                if (interactive) MessageBox.Show("Donut Agent Kit is already running. Use its existing window.", "Donut Agent Kit");
                return Emit(Result(op, new { alreadyRunning = true, pid = running[0], payloadFilesVerified = verified }), 0);
            }
            // The upstream first-run wizard waits for a Wayfern download, which is intentionally
            // disabled in this offline CBrowser kit. Replace only that wizard with START_HERE.
            // Create fresh defaults atomically; never modify an existing user's settings.
            string settingsDir = Path.Combine(State, "data", "settings");
            string settingsFile = Path.Combine(settingsDir, "app_settings.json");
            Directory.CreateDirectory(settingsDir);
            if (!File.Exists(settingsFile)) {
                try {
                    using (var stream = new FileStream(settingsFile, FileMode.CreateNew, FileAccess.Write))
                    using (var writer = new StreamWriter(stream))
                        writer.Write(Json.Serialize(new { onboarding_completed = true, disable_auto_updates = true, cloak_binary_path = Engine }));
                } catch (IOException) { if (!File.Exists(settingsFile)) throw; }
            }
            string cacheDir = Path.Combine(State, "cache");
            Directory.CreateDirectory(cacheDir);
            string geo = Path.Combine(cacheDir, "GeoLite2-City.mmdb");
            if (!File.Exists(geo)) {
                try { File.Copy(Path.Combine(Root, "assets", "GeoLite2-City.mmdb"), geo, false); }
                catch (IOException) { if (!File.Exists(geo)) throw; }
            }
            string temp = Path.Combine(State, "tmp");
            Directory.CreateDirectory(temp);
            var start = new ProcessStartInfo(App) { WorkingDirectory = Path.GetDirectoryName(App), UseShellExecute = false, CreateNoWindow = true };
            var remove = new List<string>();
            foreach (string key in start.EnvironmentVariables.Keys)
                if (key.StartsWith("DONUT", StringComparison.OrdinalIgnoreCase) || key.StartsWith("BROWSER_", StringComparison.OrdinalIgnoreCase) ||
                    key.Equals("WEBVIEW2_USER_DATA_FOLDER", StringComparison.OrdinalIgnoreCase)) remove.Add(key);
            foreach (string key in remove) start.EnvironmentVariables.Remove(key);
            start.EnvironmentVariables["DONUTBROWSER_DATA_ROOT"] = State;
            start.EnvironmentVariables["BROWSER_BINARY_PATH"] = Engine;
            start.EnvironmentVariables["BROWSER_VERSION"] = File.ReadAllLines(Path.Combine(Root, "146_Cl.txt"))[0].Trim();
            start.EnvironmentVariables["WEBVIEW2_USER_DATA_FOLDER"] = Path.Combine(State, "webview");
            start.EnvironmentVariables["TEMP"] = temp;
            start.EnvironmentVariables["TMP"] = temp;
            using (var child = StartIsolated(start)) {
                Thread.Sleep(3000);
                if (child.HasExited) throw new InvalidOperationException("manager-exited-check-webview-runtime");
                return Emit(Result(op, new { pid = child.Id, processAlive = true, payloadFilesVerified = verified,
                    dataRoot = State, liveMcpChecked = false }), 0);
            }
        } catch (Exception error) {
            string code = error is InvalidOperationException ? error.Message : "internal-error";
            if (interactive) MessageBox.Show("Cannot launch: " + code + "\nRead START_HERE.md. No profiles were imported.", "Donut Agent Kit", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return Emit(new { ok = false, operation = op, contractVersion = 1, error = new { code = code,
                stage = "preflight-or-verify", retryable = false, nextAction = "Read START_HERE.md; do not send tokens or private state to your agent" } }, error is InvalidOperationException ? 2 : 1);
        }
    }
}
