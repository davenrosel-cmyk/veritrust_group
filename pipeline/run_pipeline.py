"""
Orchestrate the Tier‑0 end‑to‑end workflow in strict deterministic order:

1. fetch SRA raw input
2. normalise → Pydantic-validated canonical models
3. write normalized intermediates (firms.json, offices.json)
4. build JSON‑LD (firms.jsonld + dataset.jsonld)
5. build manifest.jsonld (only signed artifact)
6. final logging and exit

This file contains *no business logic*.
It only orchestrates modules that each perform one responsibility.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from pipeline.utils.config_loader import load_config
from pipeline.fetch_sra import fetch_sra_from_file
from pipeline.normalize import normalise_records
from pipeline.jsonld_builder import build_and_save_jsonld
from pipeline.manifest_builder import build_manifest_and_sign


def _init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _atomic_write_json(path: Path, content: dict):
    """
    Safe atomic write for intermediates.
    Helps avoid partial writes if pipeline crashes mid-run.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except OSError as e:
        logging.error(f"Failed to write {path}: {e}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def run():
    """
    Execute the full Tier‑0 pipeline.

    Raises:
        OSError: Disk or I/O failures
        ValueError: Incorrect configuration
        RuntimeError: Errors in any sub-module
    """
    _init_logging()

    logging.info("Starting Tier‑0 pipeline…")

    cfg = load_config()

    input_path = Path(cfg.input_file)
    raw_output_dir = Path(cfg.raw_output_dir)
    normalized_output_dir = Path(cfg.normalized_output_dir)
    jsonld_firms_path = Path(cfg.jsonld_firms)
    jsonld_dataset_path = Path(cfg.jsonld_dataset)
    jsonld_manifest_path = Path(cfg.jsonld_manifest)


    raw_output_dir.mkdir(parents=True, exist_ok=True)
    normalized_output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    raw_output_path = raw_output_dir / f"sra-{today}.json"


    logging.info("Step 1 — Fetching records…")
    records = fetch_sra_from_file(input_path, raw_output_path)

   
    logging.info("Step 2 — Normalising records…")
    firms, offices = normalise_records(records)


    logging.info("Step 3 — Writing normalized intermediates…")
    firms_dict = [f.model_dump() for f in firms]
    offices_dict = [o.model_dump() for o in offices]

    _atomic_write_json(normalized_output_dir / "firms.json", firms_dict)
    _atomic_write_json(normalized_output_dir / "offices.json", offices_dict)



    logging.info("Step 4 — Building JSON‑LD (firms + dataset)…")
    build_and_save_jsonld(
        firms=firms,
        offices=offices,
        firms_output_path=jsonld_firms_path,
        dataset_output_path=jsonld_dataset_path,
    )

  
    logging.info("Step 5 — Building manifest.jsonld…")
    build_manifest_and_sign(
        firms_path=jsonld_firms_path,
        dataset_path=jsonld_dataset_path,
        manifest_output_path=jsonld_manifest_path,
    )

    logging.info("✔ Pipeline completed successfully.")
    return True


if __name__ == "__main__":
    run()
