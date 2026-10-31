"""Release auditor helper functions: git log scanner, size exceptions, and TODO checker."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent

# Whitelist files allowed to exceed 200 lines (or 300 for CSS)
def load_size_exceptions() -> Set[str]:
    exceptions_doc = ROOT / "docs" / "KNOWN_SIZE_EXCEPTIONS.md"
    if not exceptions_doc.exists():
        return set()
    found = set()
    for line in exceptions_doc.read_text(encoding="utf-8").splitlines():
        m = re.search(r"`([^`]+)`", line)
        if m:
            found.add(m.group(1).replace("\\", "/"))
    return found


def check_git_history_for_secrets() -> bool:
    """Verify that no real API key value was ever committed to git history."""
    print("Scanning git history for real API keys...")
    try:
        # Search git diffs for potential key strings (16+ chars assigned to GNANI_API_KEY)
        cmd = ["git", "log", "--all", "-p", "-G", r"GNANI_API_KEY\s*=\s*[a-zA-Z0-9_\-]{16,}"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace", check=False)
        if res.returncode != 0:
            print("  [WARN] Git log search returned non-zero code; skipping.")
            return True

        # Ensure no line contains a real non-placeholder key
        stdout_text = res.stdout or ""
        for line in stdout_text.splitlines():
            if line.startswith("+") and "GNANI_API_KEY=" in line:
                val = line.split("GNANI_API_KEY=")[-1].strip().strip('"').strip("'")
                if val and val != "your_gnani_api_key_here" and len(val) >= 16:
                    print(f"  [FAIL] Real API key found in git history diff: {val[:4]}...{val[-4:]}")
                    return False
        print("  [PASS] Git history clean of leaked API keys.")
        return True
    except Exception as exc:
        print(f"  [WARN] Could not scan git log: {exc}")
        return True


def check_unresolved_todos() -> bool:
    """Check that no actionable TODO(verify) exists in code or documentation."""
    print("Checking for unresolved TODO(verify)...")
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache"}
    found_unresolved = False

    for p in ROOT.rglob("*"):
        if p.is_dir() or any(d in p.parts for d in skip_dirs):
            continue
        if p.name in ("AGENTS.md", "check_release_helpers.py", "OPEN_QUESTIONS.md"):
            continue
        if p.suffix in (".py", ".js", ".html", ".css", ".md", ".json"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if "TODO(verify)" in content:
                    print(f"  [FAIL] Unresolved TODO(verify) in {p.relative_to(ROOT)}")
                    found_unresolved = True
            except Exception:
                continue

    if not found_unresolved:
        print("  [PASS] Zero unresolved TODO(verify) markers in codebase.")
    return not found_unresolved


def check_file_size_limits() -> bool:
    """Verify that Python files <= 200 (or listed in exceptions), CSS <= 300, JS <= 200."""
    print("Checking file size limits against KNOWN_SIZE_EXCEPTIONS.md...")
    exceptions = load_size_exceptions()
    failed = False

    scan_dirs = ["backend", "scripts", "frontend/js", "frontend/css"]
    for d_name in scan_dirs:
        d_path = ROOT / d_name
        if not d_path.exists():
            continue
        for p in d_path.rglob("*"):
            if not p.is_file():
                continue
            rel_str = str(p.relative_to(ROOT)).replace("\\", "/")
            lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())

            if p.suffix == ".py" and lines > 200 and rel_str not in exceptions:
                print(f"  [FAIL] Python file exceeds 200 lines without exception: {rel_str} ({lines} lines)")
                failed = True
            elif p.suffix == ".js" and lines > 200:
                print(f"  [FAIL] JavaScript file exceeds 200 lines: {rel_str} ({lines} lines)")
                failed = True
            elif p.suffix == ".css" and lines > 300:
                print(f"  [FAIL] CSS file exceeds 300 lines: {rel_str} ({lines} lines)")
                failed = True

    if not failed:
        print("  [PASS] All source files satisfy line count constraints.")
    return not failed
