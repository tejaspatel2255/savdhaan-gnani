from pathlib import Path
import re

def test_strings_all_keys_valid():
    content = Path("frontend/js/strings.js").read_text(encoding="utf-8")
    # Matches keys formatted as: key_name: { hi: "...", en: "...", gu: "..." }
    pattern = re.compile(
        r'^\s*([a-zA-Z0-9_]+):\s*\{\s*hi:\s*"([^"]*)",\s*en:\s*"([^"]*)",\s*gu:\s*"([^"]*)"\s*\}',
        re.MULTILINE,
    )
    matches = pattern.findall(content)
    assert len(matches) >= 60, f"Expected >= 60 string items, found {len(matches)}"

    for k, hi, en, gu in matches:
        if k == "footer_text":
            continue
        assert hi.strip(), f"Empty hi for key {k}"
        assert en.strip(), f"Empty en for key {k}"
        assert gu.strip(), f"Empty gu for key {k}"
        assert en.strip() != k, f"en string equals its own key for {k}"
