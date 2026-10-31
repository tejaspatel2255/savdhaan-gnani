"""Import, validate, and freeze blind test set calls from friend's text file."""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

MAX_CHARS_DEFAULT = 320
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+", re.IGNORECASE)
DIGITS_10_RE = re.compile(r"\b\d{10,}\b")


def parse_blind_text(content: str, max_chars: int = MAX_CHARS_DEFAULT):
    calls = []
    seen_ids = set()
    blocks = re.split(r"\n\s*\n+", content.strip())

    for block_idx, raw_block in enumerate(blocks, start=1):
        lines = [ln.strip() for ln in raw_block.splitlines() if ln.strip()]
        if not lines or all(ln.startswith("#") for ln in lines):
            continue

        meta = {}
        turns = []
        for line_num, line in enumerate(lines, start=1):
            if line.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"Block {block_idx}, line {line_num}: Malformed line (missing colon): '{line}'")
            key, val = line.split(":", 1)
            key, val = key.strip().upper(), val.strip()

            if key in ("ID", "LABEL", "TITLE", "LANG", "CUE"):
                meta[key] = val
            elif key in ("C", "L"):
                turns.append([key, val])
            else:
                raise ValueError(f"Block {block_idx}, line {line_num}: Unknown prefix '{key}:'")

        cid = meta.get("ID")
        if not cid:
            raise ValueError(f"Block {block_idx}: Missing required field 'ID'")
        if not re.match(r"^B\d+$", cid):
            raise ValueError(f"Call {cid}: ID must match 'B' followed by digits (e.g. B01, B02)")
        if cid in seen_ids:
            raise ValueError(f"Call {cid}: Duplicate ID found")
        seen_ids.add(cid)

        label = meta.get("LABEL", "").lower()
        if label not in ("scam", "legit"):
            raise ValueError(f"Call {cid}: LABEL must be 'scam' or 'legit', got '{label}'")

        title = meta.get("TITLE")
        if not title:
            raise ValueError(f"Call {cid}: Missing required field 'TITLE'")

        lang = meta.get("LANG", "hi-IN")
        if lang not in ("hi-IN", "gu-IN", "en-IN"):
            raise ValueError(f"Call {cid}: LANG must be hi-IN, gu-IN, or en-IN, got '{lang}'")

        if not (3 <= len(turns) <= 8):
            raise ValueError(f"Call {cid}: Must have between 3 and 8 turns, found {len(turns)}")

        c_turns = [t for t in turns if t[0] == "C"]
        if not c_turns:
            raise ValueError(f"Call {cid}: Must have at least one 'C' (caller) turn")

        cue_turn = None
        if "CUE" in meta:
            try:
                cue_1based = int(meta["CUE"])
                if cue_1based < 1 or cue_1based > len(turns):
                    raise ValueError(f"Call {cid}: CUE {cue_1based} out of range (1 to {len(turns)})")
                cue_turn = cue_1based - 1
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Call {cid}: CUE must be an integer, got '{meta['CUE']}'")
                raise

        total_chars = sum(len(text) for _, text in turns)
        if total_chars > max_chars:
            raise ValueError(f"Call {cid}: Total characters {total_chars} exceeds limit {max_chars}")

        for t_idx, (role, text) in enumerate(turns, start=1):
            if URL_RE.search(text):
                raise ValueError(f"Call {cid}, turn {t_idx}: Potential real URL found")
            if EMAIL_RE.search(text):
                raise ValueError(f"Call {cid}, turn {t_idx}: Potential real email found")
            for match in DIGITS_10_RE.finditer(text):
                m_str = match.group()
                if m_str != "0000000000" and not m_str.startswith("0000"):
                    raise ValueError(f"Call {cid}, turn {t_idx}: Run of 10+ digits '{m_str}' not allowed")

        call_dict = {
            "id": cid,
            "title": title,
            "label": label,
            "lang": lang,
            "cue_turn": cue_turn,
            "turns": turns,
        }
        calls.append(call_dict)

    return calls


def freeze_blind(json_bytes: bytes, num_calls: int, new_version: bool = False) -> str:
    frozen_path = Path("docs/FROZEN_BLIND.txt")
    new_hash = hashlib.sha256(json_bytes).hexdigest()
    today = datetime.date.today().isoformat()
    record_line = f"blind_calls.json: {new_hash} (date: {today}, calls: {num_calls})\n"

    if frozen_path.exists():
        existing = frozen_path.read_text(encoding="utf-8")
        if new_hash in existing:
            return new_hash
        if not new_version:
            raise RuntimeError(
                f"Hash mismatch with existing {frozen_path}. "
                "To record an updated set version, pass --new-version."
            )
        with open(frozen_path, "a", encoding="utf-8") as f:
            f.write(f"# Replaced on {today}\n{record_line}")
    else:
        frozen_path.parent.mkdir(parents=True, exist_ok=True)
        frozen_path.write_text(
            f"# FROZEN BLIND TEST SET SHA256 DIGEST\n{record_line}",
            encoding="utf-8",
        )
    return new_hash


def main():
    parser = argparse.ArgumentParser(description="Import and validate blind test set calls.")
    parser.add_argument("--input", "-i", default="data/scripts/blind_input.txt", help="Input text path")
    parser.add_argument("--output", "-o", default="data/scripts/blind_calls.json", help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing files")
    parser.add_argument("--new-version", action="store_true", help="Allow appending new hash if set changed")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file '{input_path}' not found.\n")
        sys.exit(1)

    max_chars = int(os.getenv("BLIND_MAX_CHARS", MAX_CHARS_DEFAULT))
    content = input_path.read_text(encoding="utf-8")

    try:
        calls = parse_blind_text(content, max_chars=max_chars)
    except Exception as e:
        sys.stderr.write(f"Validation Error: {e}\n")
        sys.exit(1)

    num_scam = sum(1 for c in calls if c["label"] == "scam")
    num_legit = sum(1 for c in calls if c["label"] == "legit")
    tot_chars = sum(len(txt) for c in calls for _, txt in c["turns"])

    print(f"Imported {len(calls)} calls: {num_scam} scam, {num_legit} legit.")
    if abs(num_scam - num_legit) > 2:
        print(f"Warning: Imbalance between scam ({num_scam}) and legit ({num_legit}) calls is > 2.")
    print(f"Total characters: {tot_chars}")
    print(f"TTS synthesis estimate: {tot_chars} characters (no credits used)")

    data = {"split": "blind", "calls": calls}
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

    if args.dry_run:
        print("[DRY-RUN] Validation succeeded. No files written.")
        return

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(json_bytes)
    print(f"Wrote {len(calls)} calls to {out_path}")

    h = freeze_blind(json_bytes, len(calls), new_version=args.new_version)
    print(f"Frozen in docs/FROZEN_BLIND.txt (SHA256: {h})")


if __name__ == "__main__":
    main()
