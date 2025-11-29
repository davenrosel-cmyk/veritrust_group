"""
Build dataset manifest:
    - canonical JSON serialization
    - SHA‑256 hashing
    - optional RSA signature
    - atomic file write

This is the only signed file in Tier‑0.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding



def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _try_load_private_key():
    pem = os.getenv("VT_PRIVATE_KEY_PEM")
    if not pem:
        logging.warning("VT_PRIVATE_KEY_PEM not set — manifest NOT signed.")
        return None

    try:
        return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    except (ValueError, TypeError) as e:
        logging.error("Failed to load RSA key: %s", e)
        return None


def _sign_bytes(private_key, data: bytes) -> str:
    signature = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return signature.hex()


def build_manifest_and_sign(firms_path: Path, dataset_path: Path, manifest_output_path: Path) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()

    files_info = []

    for p in [firms_path, dataset_path]:
        if p.exists():
            files_info.append(
                {
                    "path": p.name,
                    "sha256": _file_sha256(p),
                    "sizeInBytes": p.stat().st_size,
                }
            )
        else:
            logging.warning("Manifest builder: missing file → %s", p)

    manifest = {
        "@context": ["https://schema.org/", "https://veritrustgroup.org/def/tier0/"],
        "@id": "https://api.veritrustgroup.org/manifest/tier0-sra",
        "@type": "Dataset",
        "name": "VeriTrust Tier‑0 SRA Manifest",
        "dateModified": now_iso,
        "distribution": files_info,
    }

    canonical = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

    private_key = _try_load_private_key()
    if private_key:
        manifest["vt:signature"] = {
            "algorithm": "RSA-SHA256",
            "value": _sign_bytes(private_key, canonical),
        }

    tmp_path = manifest_output_path.with_suffix(manifest_output_path.suffix + ".tmp")

    try:
        manifest_output_path.parent.mkdir(parents=True, exist_ok=True)

        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        tmp_path.replace(manifest_output_path)
        logging.info("✔ manifest.jsonld written atomically → %s", manifest_output_path)

    except (OSError, IOError) as e:
        logging.error("❌ Failed to write manifest.jsonld: %s", e)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise