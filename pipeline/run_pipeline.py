"""
Orchestrates Tier‑0 end‑to‑end workflow in strict sequence:

1. fetch
2. normalise
3. validate
4. build JSON‑LD
5. build manifest
6. write AI discovery files
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from pipeline.utils.config_loader import load_config
from pipeline.fetch_sra import fetch_sra_from_file
from pipeline.normalize import normalise_records
from pipeline.validate import validate_records
from pipeline.constants import INPUT_FILENAME, RAW_OUTPUT_DIR, NORMALIZED_OUTPUT_DIR
from pipeline.manifest_builder import build_manifest_and_sign

from pipeline.jsonld_builder import build_and_save_jsonld

def run():
    logging.basicConfig(level=logging.INFO)

    cfg = load_config()

    input_path = Path(cfg["input_file"])
    raw_output_dir = Path(cfg["raw_output_dir"])
    normalized_output_dir = Path(cfg["normalized_output_dir"])

    raw_output_dir.mkdir(parents=True, exist_ok=True)
    normalized_output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    raw_output_path = raw_output_dir / f"sra-{today}.json"

    # Step 1 — Fetch
    records = fetch_sra_from_file(input_path, raw_output_path)

    # Step 2 — Normalise
    firms, offices = normalise_records(records)

    # Step 3 — Deprecated validate stub (returns unchanged)
    firms, offices = validate_records(firms, offices)

    # Save normalized intermediates
    (normalized_output_dir / "firms.json").write_text(json.dumps(firms, indent=2))
    (normalized_output_dir / "offices.json").write_text(json.dumps(offices, indent=2))

    # Step 4 — Build JSON-LD
    build_and_save_jsonld(
        firms,
        offices,
        Path(cfg["jsonld_firms"]),
        Path(cfg["jsonld_dataset"]),
    )

    # Step 5 — Manifest
    build_manifest_and_sign(
        firms_path=Path(cfg["jsonld_firms"]),
        dataset_path=Path(cfg["jsonld_dataset"]),
        manifest_output_path=Path(cfg["jsonld_manifest"]),
    )

    logging.info("✔ Pipeline completed successfully.")



if __name__ == "__main__":
    run()
