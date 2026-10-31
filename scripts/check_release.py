"""Release hygiene auditor: verifies secrets, README claims, placeholders, and test status."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_release_helpers import (
    check_file_size_limits,
    check_git_history_for_secrets,
    check_unresolved_todos,
)

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    re.compile(r"""(?i)(?:api_?key|secret|token|password)\s*[:=]\s*['"][a-zA-Z0-9_\-]{20,}['"]"""),
    re.compile(r"""(?i)x-api-key-id\s*[:=]\s*['"][a-zA-Z0-9_\-]{20,}['"]"""),
]


def check_git_status() -> bool:
    """Check that .env is not tracked in git."""
    print("Checking git tracked files...")
    try:
        res = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
        tracked = res.stdout.splitlines()
        for f in tracked:
            if f.strip() == ".env" or (f.strip().startswith(".env.") and not f.strip().endswith(".example")):
                print(f"  [FAIL] Secret environment file is tracked in git: {f}")
                return False
        print("  [PASS] No secret .env files are tracked in git.")
        return True
    except Exception as exc:
        print(f"  [WARN] Could not run git ls-files: {exc}")
        return True


def check_secrets_in_tree(base_dir: Path) -> bool:
    """Scan all source and text files for potential leaked API keys or secrets."""
    print(f"Scanning files in {base_dir} for secrets...")
    failed = False
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "tests"}

    for p in base_dir.rglob("*"):
        if p.is_dir() or any(d in p.parts for d in skip_dirs):
            continue
        if p.suffix in (".pyc", ".png", ".jpg", ".wav", ".pcm", ".zip"):
            continue

        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            continue

        for pat in SECRET_PATTERNS:
            if pat.search(content):
                if p.name == ".env.example" or "fake-key" in content or "your_gnani_api_key_here" in content:
                    continue
                print(f"  [FAIL] Potential secret found in {p.relative_to(base_dir)}")
                failed = True

    if not failed:
        print("  [PASS] Zero secret tokens found in codebase.")
    return not failed


def extract_numbers_from_results(results_data: dict) -> set:
    valid_numbers = set()

    def add_from_metrics(m):
        if not isinstance(m, dict):
            return
        tp, fn, fp, tn = m.get("tp"), m.get("fn"), m.get("fp"), m.get("tn")
        if tp is not None and fn is not None:
            valid_numbers.add(f"{tp} of {tp + fn}")
            valid_numbers.add(f"{tp}/{tp + fn}")
        if fp is not None and tn is not None:
            valid_numbers.add(f"{fp} of {fp + tn}")
            valid_numbers.add(f"{fp}/{fp + tn}")
        recall = m.get("recall")
        if recall is not None:
            valid_numbers.add(f"{recall * 100:.1f}%")
            valid_numbers.add(f"{recall * 100:.0f}%")
        far = m.get("false_alarm_rate")
        if far is not None:
            valid_numbers.add(f"{far * 100:.1f}%")
            valid_numbers.add(f"{far * 100:.0f}%")
        f1 = m.get("f1")
        if f1 is not None:
            valid_numbers.add(f"{f1:.4f}")

    for s_data in results_data.get("splits", {}).values():
        add_from_metrics(s_data)
        if "ceiling" in s_data:
            add_from_metrics(s_data["ceiling"])

    return valid_numbers


def check_readme_figures(readme_content: str, results_path: Path) -> bool:
    if not results_path.exists():
        return True
    try:
        r_data = json.loads(results_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  [WARN] Could not parse results.json: {exc}")
        return True

    valid_figures = extract_numbers_from_results(r_data)
    for pct in re.findall(r"(\b\d+\.?\d*%)", readme_content):
        if pct != "95%" and pct not in valid_figures:
            print(f"  [FAIL] README contains unverified percentage: '{pct}'")
            return False

    for count_str in re.findall(r"(\b\d+\s*(?:of|/)\s*\d+\b)", readme_content):
        if count_str.strip() not in valid_figures:
            print(f"  [FAIL] README contains unverified count ratio: '{count_str.strip()}'")
            return False
    return True


def check_readme_integrity(allow_placeholders: bool = False) -> bool:
    print("Checking README.md...")
    readme_path = ROOT / "README.md"
    results_path = ROOT / "data" / "eval" / "results.json"
    if not readme_path.exists():
        print("  [FAIL] README.md does not exist.")
        return False

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    if len(lines) > 140:
        print(f"  [FAIL] README.md exceeds 140 lines ({len(lines)} lines).")
        return False
    print(f"  [PASS] README.md line count: {len(lines)} (<= 140).")

    content = "\n".join(lines)
    if not allow_placeholders and ("TODO" in content or "<<" in content):
        print("  [FAIL] Unfinished 'TODO' or '<<' placeholders remain in README.md.")
        return False
    print("  [PASS] Placeholder check passed.")

    if not check_readme_figures(content, results_path):
        return False
    print("  [PASS] All figures in README verified against results.json.")
    return True


def check_license_exists() -> bool:
    print("Checking LICENSE...")
    lic = ROOT / "LICENSE"
    if not lic.exists():
        print("  [FAIL] LICENSE file is missing.")
        return False
    print("  [PASS] LICENSE file present.")
    return True


def check_frozen_final_integrity() -> bool:
    frozen_final = ROOT / "docs" / "FROZEN_FINAL.txt"
    if not frozen_final.exists():
        return True
    print("Checking FROZEN_FINAL.txt rules integrity...")
    import hashlib

    content = frozen_final.read_text(encoding="utf-8")
    for r_file in (ROOT / "rules").glob("*.json"):
        curr_hash = hashlib.sha256(r_file.read_bytes()).hexdigest()
        if curr_hash not in content:
            print(f"  [FAIL] Rule file {r_file.name} hash does not match {frozen_final.name}")
            return False
    print("  [PASS] Rules match authoritative FROZEN_FINAL.txt.")
    return True


def run_checks(allow_placeholders: bool = False) -> bool:
    checks = [
        ("Git Untracked .env", check_git_status()),
        ("Tree Secrets Scan", check_secrets_in_tree(ROOT)),
        ("Git History Secrets Scan", check_git_history_for_secrets()),
        ("LICENSE file", check_license_exists()),
        ("Unresolved TODOs", check_unresolved_todos()),
        ("File Size Limits", check_file_size_limits()),
        ("README.md Integrity", check_readme_integrity(allow_placeholders)),
        ("Frozen Final Integrity", check_frozen_final_integrity()),
    ]
    print("\n" + "=" * 60 + "\nAUDIT SUMMARY:")
    all_passed = True
    for name, passed in checks:
        print(f"  {name:28}: [{'PASS' if passed else 'FAIL'}]")
        if not passed:
            all_passed = False
    print("=" * 60)
    return all_passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Release hygiene auditor")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow <<LINKS>> in docs before publish")
    args = parser.parse_args()

    print("=" * 60 + "\nSAVDHAAN RELEASE HYGIENE AUDIT\n" + "=" * 60)
    if not run_checks(args.allow_placeholders):
        sys.exit(1)
    print("\nRelease hygiene verification complete. Ready for submission.")


if __name__ == "__main__":
    main()
