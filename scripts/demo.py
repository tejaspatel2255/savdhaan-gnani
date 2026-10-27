"""Demo runner for Savdhaan in zero-credit, offline mode."""

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn


def check_demo_prerequisites() -> bool:
    """Check required offline files exist before starting demo server."""
    mock_file = Path("data/mock/mock_call.json")
    if not mock_file.exists():
        print(f"Error: Missing demo mock file: {mock_file}", file=sys.stderr)
        print("Run Phase 0 setup or restore data/mock/mock_call.json to create it.", file=sys.stderr)
        return False

    sample_run = Path("frontend/assets/sample_run.jsonl")
    if not sample_run.exists():
        print(f"Error: Missing sample run file: {sample_run}", file=sys.stderr)
        print("Ensure frontend/assets/sample_run.jsonl exists for demo playback.", file=sys.stderr)
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Savdhaan in offline DEMO mode")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    args = parser.parse_args()

    if not check_demo_prerequisites():
        sys.exit(1)

    # Enable DEMO mode
    os.environ["DEMO"] = "1"

    print("=" * 65)
    print("SAVDHAAN DEMO MODE (Offline · Zero Credits · Synthetic Only)")
    print(f"Serving at http://{args.host}:{args.port}")
    print("=" * 65)

    uvicorn.run("backend.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
