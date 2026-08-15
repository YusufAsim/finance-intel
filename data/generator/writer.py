"""Output helpers.

Files are written with a fixed layout and LF endings so two runs with the
same seed can be compared byte by byte.
"""

import json
from pathlib import Path


def _dump(payload: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def transactions_path(out_dir: Path, profile: str, seed: int) -> Path:
    return out_dir / f"transactions_{profile}_{seed}.json"


def write_transactions(
    transactions: list[dict], out_dir: Path, profile: str, seed: int
) -> Path:
    return _dump(transactions, transactions_path(out_dir, profile, seed))
