"""
Fetch and load the SRA public dataset (Tier‑0 raw acquisition).

Responsibilities:
    - deterministic loading of local SRA JSON input
    - accept both dict-based ("Organisations": [...]) and list-based inputs
    - write raw dump atomically for audit (Phase‑3)
    - perform no transformation, no enrichment

Validation:
    - basic structural checks only
    - deep validation occurs in normalisation stage (Pydantic)

This module is intentionally minimal.
"""

import json
import logging
from pathlib import Path
from typing import List, Union
from pipeline.utils.atomic_writer import atomic_write_json
import requests
from datetime import datetime, timezone

def _load_json(path: Path) -> Union[dict, list]:
    """
    Safely load JSON from disk with explicit exception handling.

    Args:
        path: Path to the input JSON file.

    Returns:
        Parsed Python object (dict or list).

    Raises:
        FileNotFoundError
        json.JSONDecodeError
        OSError
    """


    if not path.exists():
        raise FileNotFoundError(f"SRA input file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logging.error(f"❌ Invalid JSON in {path}: {e}")
        raise

    except OSError as e:
        logging.error(f"❌ Failed to read file {path}: {e}")
        raise


def fetch_sra_from_file(input_file: Path, save_path: Path , fetch_url: str, subscription_key: str) -> List[dict]:
    """
    Load SRA dataset from a local JSON file.

    Accepts:
        A) {"Organisations": [ ... ]}
        B) [ ... ]   (used in testing fixtures)

    Writes an atomic raw dump to save_path for audit.

    Args:
        input_file: Local SRA JSON dump.
        save_path: Path where raw canonical dump will be written atomically.

    Returns:
        The list of raw organisation records.

    Raises:
        ValueError: if structure is unexpected.
        OSError: file write errors.
    """

    now_gmt = datetime.now(timezone.utc)
    formatted = now_gmt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    headers = {
        "Ocp-Apim-Subscription-Key":subscription_key
        #"date":"Wed, 03 Dec 2025 21:04:18 GMT"
        # "date":formatted
    }

    response = requests.get(fetch_url, headers=headers)

    # theHeader = response.headers
    # resDate = theHeader.get("Date", "")
    theText = response.text  
    # retrievedAt
    # theAddedtext = f'\n/* Retrieved at {formatted} */\n' + theText

    strrr = f""" "retrievedAt":"{formatted}" ,  """

    # new_string = original[:1] + insert + original[1:]
    theText = theText[:1] + strrr + theText[1:]



    with open(input_file, "w", encoding="utf-8") as file:
        file.write(theText)

    logging.info("Fetching SRA dataset from %s", input_file)

    data = _load_json(input_file)

  
    if isinstance(data, dict):
        organisations = data.get("Organisations", [])
        if not isinstance(organisations, list):
            raise ValueError("Expected Organisations to be a list")

    
    elif isinstance(data, list):
        organisations = data

    else:
        raise ValueError(f"Unexpected SRA input type: {type(data)}")

    atomic_write_json(save_path, organisations)

    return organisations
#     save_path.parent.mkdir(parents=True, exist_ok=True)
#     tmp_path = save_path.with_suffix(save_path.suffix + ".tmp")

#     try:
#         with tmp_path.open("w", encoding="utf-8") as f:
#             json.dump(organisations, f, ensure_ascii=False, indent=2)

#         tmp_path.replace(save_path)
#         logging.info("✔ Atomic raw dump written → %s", save_path)

#     except OSError as e:
#         logging.error(f"❌ Failed to write raw dump {save_path}: {e}")
#         if tmp_path.exists():
#             tmp_path.unlink(missing_ok=True)
#         raise

#     return organisations


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)

#     test_path = Path("input/response.txt")
#     out = Path("output/raw/test_raw.json")

#     recs = fetch_sra_from_file(test_path, out)
#     print(f"Loaded {len(recs)} records")
