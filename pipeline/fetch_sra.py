

import json
import logging
from pathlib import Path
from datetime import datetime


def fetch_sra_from_file(input_file: Path, save_path: Path) -> list[dict]:
    """
    Load the SRA dataset from a local JSON file (response.txt).
    Expect structure:
    {
        "Count": N,
        "Organisations": [ ... ]
    }
    Returns Organisations[].
    """

    logging.info("Loading SRA dataset from local file: %s", input_file)

    if not input_file.exists():
        raise FileNotFoundError(f"SRA input file not found: {input_file}")

    with input_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    organisations = data.get("Organisations", [])

    logging.info("Loaded %d organisations from response.txt", len(organisations))

    # Save raw audit copy
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with save_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return organisations


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    input_path = Path("input/response.txt")
    today = datetime.now().strftime("%Y%m%d")
    raw_path = Path(f"output/raw/sra-{today}.json")

    records = fetch_sra_from_file(input_path, raw_path)
    print(f"Loaded {len(records)} records")
