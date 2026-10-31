"""Release freeze orchestrator: runs all audit gates, writes RELEASE.txt on --go, and outputs final git commands."""

import argparse
import datetime
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_cmd(cmd: list) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    return res.returncode, res.stdout + res.stderr


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Savdhaan release freeze gate")
    parser.add_argument("--go", action="store_true", help="Authorize freeze and write docs/RELEASE.txt")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow documentation placeholders before public posting")
    args = parser.parse_args()

    print("=" * 65)
    print("SAVDHAAN FINAL RELEASE FREEZE GATE")
    print("=" * 65)

    # 1. Verify static site structure and Vercel configuration
    print("\n[Gate 1/3] Verifying static bundle and Vercel config...")
    code, out = run_cmd([sys.executable, "scripts/verify_static_site.py"])
    print(out.strip())
    if code != 0:
        print("\n[BLOCKED] Gate 1 failed. Static site verification failed.")
        sys.exit(1)

    # 2. Run release hygiene auditor
    print("\n[Gate 2/3] Running release hygiene auditor...")
    check_args = [sys.executable, "scripts/check_release.py"]
    if args.allow_placeholders:
        check_args.append("--allow-placeholders")
    code, out = run_cmd(check_args)
    print(out.strip())
    if code != 0:
        print("\n[BLOCKED] Gate 2 failed. Release hygiene audit failed.")
        sys.exit(1)

    # 3. Quick test suite validation
    print("\n[Gate 3/3] Running test suite gate...")
    code, out = run_cmd([sys.executable, "-m", "pytest", "tests/test_verify_static.py", "tests/test_english_first.py", "tests/test_frontend_static.py", "-q"])
    print(out.strip())
    if code != 0:
        print("\n[BLOCKED] Gate 3 failed. Unit test verification failed.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("ALL RELEASE FREEZE GATES PASSED CLEANLY")
    print("=" * 65)

    if not args.go:
        print("\nDRY-RUN COMPLETE: No files were frozen.")
        print("To officially seal the release and write docs/RELEASE.txt, run:")
        print("  python scripts/release_freeze.py --go --allow-placeholders")
        return

    # Write docs/RELEASE.txt
    release_txt = ROOT / "docs" / "RELEASE.txt"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines = [
        "SAVDHAAN OFFICIAL RELEASE SEAL",
        f"Timestamp: {timestamp}",
        "Competition: Great Indian AI Internship Challenge (Gnani AI)",
        "Challenge Deadline: Nov 10, 2026, 11:59 PM IST",
        "",
        "Authoritative File Checksums (SHA256):",
    ]

    target_files = [
        ROOT / "README.md",
        ROOT / "docs" / "SUBMISSION.md",
        ROOT / "frontend" / "index.html",
        ROOT / "frontend" / "report.html",
        ROOT / "frontend" / "assets" / "results.json",
        ROOT / "frontend" / "assets" / "audio" / "manifest.json",
    ] + sorted(ROOT.glob("rules/*.json"))

    for tf in target_files:
        if tf.exists():
            rel_name = str(tf.relative_to(ROOT)).replace("\\", "/")
            lines.append(f"  {rel_name}: {compute_file_sha256(tf)}")

    release_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[SEALED] Created authoritative freeze manifest at: docs/RELEASE.txt")

    print("\nNEXT USER ACTIONS:")
    print("  1. Review your changes:")
    print("       git status")
    print("  2. Stage and commit the final submission release:")
    print("       git add .")
    print('       git commit -m "Phase 17: Deploy check, submission package, and the final release freeze"')
    print("  3. Tag the release:")
    print('       git tag -a v1.0.0 -m "Savdhaan v1.0.0 submission release"')
    print("  4. Push commit and tag to GitHub:")
    print("       git push origin main")
    print("       git push origin v1.0.0")
    print("  5. Import repo into Vercel and verify your live demo link!")


if __name__ == "__main__":
    main()
