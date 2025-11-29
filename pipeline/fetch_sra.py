
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



def fetch_sra_from_file(input_file: Path, save_path: Path) -> List[RawFirmRecord]:
    """
    Load local SRA response (response.txt).
    Saves the raw JSON atomically.
    Returns list of Organisations[].
    """
    logging.info("Loading SRA dataset from: %s", input_file)

    data = _load_local_file(input_file)
    organisations = data.get("Organisations", [])

    logging.info("Loaded %d organisations", len(organisations))

    # --- Phase 3: Atomic Write ---
    tmp_path = save_path.with_suffix(save_path.suffix + ".tmp")

    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        tmp_path.replace(save_path)

        logging.info(f"✔ Atomically written raw SRA file → {save_path}")

    except Exception as e:
        logging.error(f"❌ Failed to write raw SRA file {save_path}: {e}")

        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

        raise

    return organisations




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    input_path = Path("input/response.txt")
    today = datetime.now().strftime("%Y%m%d")
    raw_path = Path(f"output/raw/sra-{today}.json")

    records = fetch_sra_from_file(input_path, raw_path)
    print(f"Loaded {len(records)} records")
