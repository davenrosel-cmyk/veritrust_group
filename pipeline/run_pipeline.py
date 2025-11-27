import json
import logging
from pathlib import Path
from datetime import datetime

from fetch_sra import fetch_sra_from_file
from normalize import normalise_records
from validate import validate_records
from constants import INPUT_FILENAME, RAW_OUTPUT_DIR, NORMALIZED_OUTPUT_DIR


def run():
    logging.basicConfig(level=logging.INFO)

    input_path = Path(INPUT_FILENAME)

    today = datetime.now().strftime("%Y%m%d")
    raw_path = Path(RAW_OUTPUT_DIR) / f"sra-{today}.json"

    # Step 1 — Load local SRA data
    records = fetch_sra_from_file(input_path, raw_path)

    # Step 2 — Normalise
    firms, offices = normalise_records(records)

    # Step 3 — Validate
    valid_firms, valid_offices = validate_records(firms, offices)

   
    out_dir = Path(NORMALIZED_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "firms.json").write_text(json.dumps(valid_firms, indent=2))
    (out_dir / "offices.json").write_text(json.dumps(valid_offices, indent=2))

    logging.info("Pipeline completed successfully.")


if __name__ == "__main__":
    run()
