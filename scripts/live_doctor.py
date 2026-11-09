"""Local live doctor: diagnoses why 'Listen live' may not be running locally.
Zero Gnani API calls; never prints or leaks secrets.
"""
import os
import socket
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def diagnose_live(env_path: Path = None, port: int = 8000) -> dict:
    env_file = env_path if env_path is not None else (ROOT / ".env")
    report = {
        "checks": [],
        "all_pass": True,
        "instructions": []
    }

    def add_check(name: str, passed: bool, detail: str, fix: str = ""):
        report["checks"].append({"name": name, "passed": passed, "detail": detail, "fix": fix})
        if not passed:
            report["all_pass"] = False
            if fix:
                report["instructions"].append(fix)

    # 1. Check .env exists & GNANI_API_KEY
    if not env_file.exists():
        add_check(".env file", False, "missing", "Create a .env file with GNANI_API_KEY=your_key")
        add_check("GNANI_API_KEY", False, "missing", "Set GNANI_API_KEY in .env (never commit it)")
    else:
        add_check(".env file", True, "present", "")
        key_found = False
        lines = env_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if line.strip().startswith("GNANI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    key_found = True
                    break
        if key_found:
            add_check("GNANI_API_KEY", True, "present", "")
        else:
            add_check("GNANI_API_KEY", False, "missing or empty", "Put your real Gnani key into .env")

    # 2. Check DEMO env var
    demo_val = os.environ.get("DEMO", "").strip()
    if demo_val == "1":
        add_check("DEMO mode", False, "DEMO=1 is set", "Unset DEMO env var so live listening is enabled")
    else:
        add_check("DEMO mode", True, "not set to 1", "")

    # 3. Check ALLOW_REMOTE_LIVE
    allow_remote = os.environ.get("ALLOW_REMOTE_LIVE", "0").strip()
    add_check("ALLOW_REMOTE_LIVE", True, f"state: {allow_remote}", "")

    # 4. Check assets and rules directories
    rules_present = (ROOT / "rules" / "scam_rules_hi_en.json").exists()
    add_check("Scam rules", rules_present, "present" if rules_present else "missing", "Ensure rules/scam_rules_hi_en.json exists")

    # 5. Check Python version
    py_ok = sys.version_info >= (3, 10)
    add_check("Python version", py_ok, f"{sys.version_info.major}.{sys.version_info.minor}", "Use Python 3.10 or newer")

    # 6. Check websockets
    try:
        import websockets
        ws_ok = True
        ws_ver = getattr(websockets, "__version__", "unknown")
    except ImportError:
        ws_ok = False
        ws_ver = "missing"
    add_check("websockets package", ws_ok, ws_ver, "Run: pip install 'websockets>=13.0'")

    # 7. Check server status on port
    server_running = False
    key_reported = None
    try:
        url = f"http://127.0.0.1:{port}/api/health"
        req = urllib.request.Request(url, headers={"User-Agent": "SavdhaanDoctor/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            import json
            data = json.loads(resp.read().decode("utf-8"))
            server_running = True
            key_reported = data.get("gnani_key_present")
    except Exception:
        server_running = False

    if server_running:
        status_msg = f"active (gnani_key_present: {key_reported})"
        fix_msg = "" if key_reported else "Server is up but has no Gnani key. Check .env and restart server."
        add_check(f"Server on port {port}", bool(key_reported), status_msg, fix_msg)
    else:
        # Check if port is open or free
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        port_free = (res != 0)
        detail = "free (server not started)" if port_free else "port occupied by another process"
        add_check(f"Server on port {port}", False, detail, f"Start server: python -m uvicorn backend.main:app --port {port}")

    return report


def main():
    print("=" * 60)
    print("SAVDHAAN LOCAL LIVE DOCTOR")
    print("=" * 60)
    rep = diagnose_live()
    for c in rep["checks"]:
        tag = "[PASS]" if c["passed"] else "[FAIL]"
        print(f"  {tag:6} {c['name']:<25}: {c['detail']}")

    print("=" * 60)
    if rep["all_pass"]:
        print("ALL CHECKS PASSED: Open http://localhost:8000 and click 'Listen live'")
    else:
        print("ACTION REQUIRED TO RUN LIVE:")
        for i, inst in enumerate(rep["instructions"], 1):
            print(f"  {i}. {inst}")
        print("\nCommand to start backend:")
        print("  python -m uvicorn backend.main:app --port 8000")
        print("Then open in browser:")
        print("  http://localhost:8000")
    print("=" * 60)
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
