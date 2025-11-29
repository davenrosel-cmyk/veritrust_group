
"""
Fetch SRA public dataset.
Downloads JSON from SRA endpoint, writes raw dump to output/raw
for audit and passes data to the normalisation stage.

Tier‑0 rule:
    - No enrichments
    - No transformations except saving raw
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from pipeline.models.raw_models import RawFirmRecord


def _load_local_file(path: Path) -> dict:
    """
    Safe JSON reader with explicit error handling.
    Phase 3: strengthened I/O reliability (read side).
    """
    if not path.exists():
        raise FileNotFoundError(f"SRA input file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logging.error(f"❌ Failed to parse JSON from {path}: {e}")
        raise

    except Exception as e:
        logging.error(f"❌ Failed to read file {path}: {e}")
        raise



def fetch_sra_from_file(input_file: Path, save_path: Path) -> list[dict]:
    """
    Load local SRA response (response.txt).
    Supports:
        A) {"Organisations": [ ... ]}
        B) [ ... ]   (test fixture / simplified files)

    Saves raw JSON atomically to save_path.
    """

    logging.info("Loading SRA dataset from: %s", input_file)

    data = _load_local_file(input_file)

    # A) If dict with Organisations
    if isinstance(data, dict):
        organisations = data.get("Organisations", [])

        if not isinstance(organisations, list):
            raise ValueError("Organisations is not a list in SRA input file")

    # B) If test provided a list directly
    elif isinstance(data, list):
        organisations = data

    else:
        raise ValueError(f"Unexpected SRA input format: {type(data)}")

    # Atomic save
    save_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = save_path.with_suffix(save_path.suffix + ".tmp")

    with tmp.open("w", encoding="utf-8") as f:
        json.dump(organisations, f, ensure_ascii=False, indent=2)

    tmp.replace(save_path)

    return organisations



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    input_path = Path("input/response.txt")
    today = datetime.now().strftime("%Y%m%d")
    raw_path = Path(f"output/raw/sra-{today}.json")

    records = fetch_sra_from_file(input_path, raw_path)
    print(f"Loaded {len(records)} records")
