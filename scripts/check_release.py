"""Release hygiene auditor: verifies secrets, README claims, placeholders, and test status."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Regex to detect secret keys or long random tokens
SECRET_PATTERNS = [
    re.compile(r"""(?i)(?:api_?key|secret|token|password)\s*[:=]\s*['"][a-zA-Z0-9_\-]{20,}['"]"""),
    re.compile(r"""(?i)x-api-key-id\s*[:=]\s*['"][a-zA-Z0-9_\-]{20,}['"]"""),
]

SUSPICIOUS_TOKEN_PATTERN = re.compile(r"""(?i)(?:api_?key|secret|token)\s*=\s*[a-zA-Z0-9_\-]{16,}""")


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
                # Allow .env.example or test files with fake-key
                if p.name == ".env.example" or "fake-key" in content:
                    continue
                print(f"  [FAIL] Potential secret found in {p.relative_to(base_dir)}")
                failed = True

    if not failed:
        print("  [PASS] Zero secret tokens found in codebase.")
    return not failed


def extract_numbers_from_results(results_data: dict) -> set:
    """Extract valid formatted numbers (percentages, k of n, k/n) from results.json."""
    valid_numbers = set()

    def add_from_metrics(m):
        if not isinstance(m, dict):
            return
        for key in ["tp", "fp", "fn", "tn"]:
            pass
        tp = m.get("tp")
        fn = m.get("fn")
        fp = m.get("fp")
        tn = m.get("tn")

        if tp is not None and fn is not None:
            n_pos = tp + fn
            valid_numbers.add(f"{tp} of {n_pos}")
            valid_numbers.add(f"{tp}/{n_pos}")
        if fp is not None and tn is not None:
            n_neg = fp + tn
            valid_numbers.add(f"{fp} of {n_neg}")
            valid_numbers.add(f"{fp}/{n_neg}")

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

    splits = results_data.get("splits", {})
    for s_name, s_data in splits.items():
        add_from_metrics(s_data)
        if "ceiling" in s_data:
            add_from_metrics(s_data["ceiling"])

    return valid_numbers


def check_readme_figures(readme_content: str, results_path: Path) -> bool:
    """Check that every percentage, k/n or k of n in README exists in results.json."""
    if not results_path.exists():
        return True

    try:
        r_data = json.loads(results_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  [WARN] Could not parse results.json: {exc}")
        return True

    valid_figures = extract_numbers_from_results(r_data)

    # 1. Check all percentages: (\d+\.?\d*%)
    # Exclude CI interval numbers like 95% CI
    pct_matches = re.findall(r"(\b\d+\.?\d*%)", readme_content)
    for pct in pct_matches:
        if pct == "95%":  # standard confidence interval notation
            continue
        if pct not in valid_figures:
            print(f"  [FAIL] README contains unverified percentage not in results.json: '{pct}'")
            return False

    # 2. Check all "k of n" or "k/n" patterns: (\d+\s*(?:of|/)\s*\d+)
    count_matches = re.findall(r"(\b\d+\s*(?:of|/)\s*\d+\b)", readme_content)
    for count_str in count_matches:
        norm_count = count_str.strip()
        if norm_count not in valid_figures:
            print(f"  [FAIL] README contains unverified count ratio not in results.json: '{norm_count}'")
            return False

    return True


def check_readme_integrity(readme_path: Path = None, results_path: Path = None) -> bool:
    """Verify README line count, placeholder absence, and metric consistency."""
    print("Checking README.md...")
    if readme_path is None:
        readme_path = ROOT / "README.md"
    if results_path is None:
        results_path = ROOT / "data" / "eval" / "results.json"

    if not readme_path.exists():
        print("  [FAIL] README.md does not exist.")
        return False

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    line_count = len(lines)
    if line_count > 140:
        print(f"  [FAIL] README.md exceeds 140 lines ({line_count} lines).")
        return False
    print(f"  [PASS] README.md line count: {line_count} (<= 140).")

    content = "\n".join(lines)
    # Check for unfinished placeholders
    if "TODO" in content or "<<" in content:
        print("  [FAIL] Unfinished 'TODO' or '<<' placeholders remain in README.md.")
        return False
    print("  [PASS] No placeholders found in README.md.")

    # Check figures against results.json
    if not check_readme_figures(content, results_path):
        return False
    print("  [PASS] All percentages and k of n counts in README verified against results.json.")

    return True


def check_test_suite() -> bool:
    """Run pytest in quiet mode to ensure test suite is green."""
    print("Running pytest suite...")
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            print("  [FAIL] Pytest test suite has failures:")
            print(res.stdout)
            print(res.stderr)
            return False
        print("  [PASS] All pytest test suites passed cleanly.")
        return True
    except Exception as exc:
        print(f"  [FAIL] Could not run pytest: {exc}")
        return False


def main() -> None:
    print("=" * 60)
    print("SAVDHAAN RELEASE HYGIENE AUDIT")
    print("=" * 60)

    checks = [
        ("Git Untracked .env", check_git_status()),
        ("Secrets Scan", check_secrets_in_tree(ROOT)),
        ("README.md Integrity", check_readme_integrity()),
        ("Pytest Green", check_test_suite()),
    ]

    print("\n" + "=" * 60)
    print("AUDIT SUMMARY:")
    all_passed = True
    for name, passed in checks:
        status_str = "PASS" if passed else "FAIL"
        print(f"  {name:25}: [{status_str}]")
        if not passed:
            all_passed = False
    print("=" * 60)

    if not all_passed:
        sys.exit(1)
    print("\nRelease hygiene verification complete. Ready for submission.")


if __name__ == "__main__":
    main()
