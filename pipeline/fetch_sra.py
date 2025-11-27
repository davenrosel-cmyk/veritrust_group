

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from models import RawFirmRecord


def _load_local_file(path: Path) -> dict:
    """Internal helper. Loads JSON from disk."""
    if not path.exists():
        raise FileNotFoundError(f"SRA input file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_sra_from_file(input_file: Path, save_path: Path) -> List[RawFirmRecord]:
    """
    Load local SRA response (response.txt).
    Returns list of Organisations[].
    """
    logging.info("Loading SRA dataset from: %s", input_file)

    data = _load_local_file(input_file)
    organisations = data.get("Organisations", [])

    logging.info("Loaded %d organisations", len(organisations))

    
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with save_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return organisations



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    input_path = Path("input/response.txt")
    today = datetime.now().strftime("%Y%m%d")
    raw_path = Path(f"output/raw/sra-{today}.json")

    records = fetch_sra_from_file(input_path, raw_path)
    print(f"Loaded {len(records)} records")
