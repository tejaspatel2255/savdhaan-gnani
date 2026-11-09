"""Exports backend/scorer and rules into frontend/assets/pyscorer/ for in-browser scoring."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_SCORER = ROOT / "backend" / "scorer"
SRC_RULES = ROOT / "rules"
DEST_ROOT = ROOT / "frontend" / "assets" / "pyscorer"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def export_pyscorer():
    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    dest_backend_scorer = DEST_ROOT / "backend" / "scorer"
    dest_rules = DEST_ROOT / "rules"
    dest_backend_scorer.mkdir(parents=True, exist_ok=True)
    dest_rules.mkdir(parents=True, exist_ok=True)

    # Files to copy
    scorer_files = ["__init__.py", "engine.py", "matching.py", "normalize.py", "rules_loader.py"]
    rules_files = ["scam_rules_hi_en.json", "scam_rules_gu.json"]

    manifest = {"files": {}}

    for fname in scorer_files:
        src = SRC_SCORER / fname
        dst = dest_backend_scorer / fname
        shutil.copy2(src, dst)
        h = sha256_file(src)
        manifest["files"][f"backend/scorer/{fname}"] = {"sha256": h}

    for fname in rules_files:
        src = SRC_RULES / fname
        dst = dest_rules / fname
        shutil.copy2(src, dst)
        h = sha256_file(src)
        manifest["files"][f"rules/{fname}"] = {"sha256": h}

    # Write manifest
    manifest_path = DEST_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Exported {len(manifest['files'])} files to {DEST_ROOT} with manifest.json")


def verify_pyscorer_integrity() -> bool:
    manifest_path = DEST_ROOT / "manifest.json"
    if not manifest_path.exists():
        print("FAIL: frontend/assets/pyscorer/manifest.json missing. Run: python scripts/export_pyscorer.py")
        return False

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel_path, meta in manifest.get("files", {}).items():
        src_path = ROOT / rel_path
        dst_path = DEST_ROOT / rel_path
        if not src_path.exists() or not dst_path.exists():
            print(f"FAIL: Missing file {rel_path}. Run: python scripts/export_pyscorer.py")
            return False
        h_src = sha256_file(src_path)
        h_dst = sha256_file(dst_path)
        if h_src != meta["sha256"] or h_dst != meta["sha256"]:
            print(f"FAIL: Drift detected in {rel_path}. Run: python scripts/export_pyscorer.py")
            return False
    return True


if __name__ == "__main__":
    export_pyscorer()
    if not verify_pyscorer_integrity():
        sys.exit(1)
    print("pyscorer export and verification successful.")
