"""
Build Tier‑0 dataset manifest:

Features:
    - canonical JSON serialization (Phase‑4)
    - SHA‑256 hashing for all distributed files
    - optional RSA‑SHA256 signature using VT_PRIVATE_KEY_PEM
    - strict error handling (no generic Exception)
    - atomic file write (Phase‑3)
    - deterministic output

This is the *only* signed artifact in Tier‑0.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from pipeline.utils.atomic_writer import atomic_write_json
from cryptography.exceptions import InvalidKey, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding




def _file_sha256(path: Path) -> str:
    """
    Compute SHA‑256 hash of a file using a safe streaming method.

    Args:
        path: Path to a file on disk.

    Returns:
        Hexadecimal SHA‑256 digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _try_load_private_key():
    """
    Load RSA private key from environment variable VT_PRIVATE_KEY_PEM.

    Returns:
        Loaded private key object or None if unavailable or invalid.
    """
    pem = os.getenv("VT_PRIVATE_KEY_PEM")

    if not pem:
        logging.warning("VT_PRIVATE_KEY_PEM not set — manifest will not be signed.")
        return None

    try:
        return serialization.load_pem_private_key(
            pem.encode("utf-8"),
            password=None,
        )
    except (ValueError, TypeError, UnsupportedAlgorithm, InvalidKey) as e:
        logging.error("Failed to load RSA private key: %s", e)
        return None


def _sign_bytes(private_key, canonical_bytes: bytes) -> str:
    """
    Sign canonical JSON bytes using RSA-SHA256.

    Args:
        private_key: Loaded RSA private key.
        canonical_bytes: Canonical JSON UTF‑8 bytes.

    Returns:
        Hex signature.
    """
    try:
        signature = private_key.sign(
            canonical_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return signature.hex()

    except (ValueError, TypeError) as e:
        logging.error("RSA signing failed: %s", e)
        raise


def build_manifest_and_sign(
    firms_path: Path,
    dataset_path: Path,
    manifest_output_path: Path,
) -> None:

    now_iso = datetime.now(timezone.utc).isoformat()

    files_info = []

    for p in [firms_path, dataset_path]:
        if not p.exists():
            logging.warning("Manifest: Missing file → %s", p)
            continue

        files_info.append(
            {
                "path": p.name,
                "sha256": _file_sha256(p),
                "sizeInBytes": p.stat().st_size,
            }
        )

    manifest = {
        "@context": [
            "https://schema.org/",
            "https://veritrustgroup.org/def/tier0/",
        ],
        "@id": "https://api.veritrustgroup.org/manifest/tier0-sra",
        "@type": "Dataset",
        "name": "VeriTrust Tier‑0 SRA Manifest",
        "dateModified": now_iso,
        "distribution": files_info,
    }

    canonical_json = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    private_key = _try_load_private_key()

    if private_key:
        signature_hex = _sign_bytes(private_key, canonical_json)
        manifest["vt:signature"] = {
            "algorithm": "RSA-SHA256",
            "value": signature_hex,
        }

    atomic_write_json(manifest_output_path, manifest)

    logging.info("✔ manifest.jsonld built and saved → %s", manifest_output_path)