# pipeline/utils/atomic_writer.py

"""
Shared atomic write utilities for Tier‑0 pipeline.

Features:
    - atomic write for JSON (indent=2 human‑readable)
    - atomic write for raw bytes (manifest signing, etc.)
    - safe cleanup of temp files
    - deterministic UTF‑8 output
    - strict error handling (no generic Exception)

Used by:
    - run_pipeline.py
    - fetch_sra.py
    - jsonld_builder.py
    - manifest_builder.py
"""

import json
import logging
from pathlib import Path


def atomic_write_json(path: Path, data) -> None:
    """
    Atomically write a JSON document with indent=2 (human‑readable).
    Writes to <path>.tmp first, then replaces final file.

    Args:
        path: Final output path
        data: JSON‑serializable object
    """
    tmp = path.with_suffix(path.suffix + ".tmp")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with tmp.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        tmp.replace(path)
        logging.info(f"✔ Atomic JSON write → {path}")

    except OSError as e:
        logging.error(f"❌ Failed to write JSON file {path}: {e}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """
    Atomically write raw bytes.
    Used for signed artifacts in later phases.

    Args:
        path: Final output path
        content: Raw bytes
    """
    tmp = path.with_suffix(path.suffix + ".tmp")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with tmp.open("wb") as f:
            f.write(content)

        tmp.replace(path)
        logging.info(f"✔ Atomic bytes write → {path}")

    except OSError as e:
        logging.error(f"❌ Failed to write bytes file {path}: {e}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise
