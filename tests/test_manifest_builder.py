"""
Tier‑0 Manifest Builder (Phase‑3)
 - canonical JSON
 - SHA‑256 hashing
 - optional RSA signature
 - atomic write
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


def _load_private_key():
    pem = os.getenv("VT_PRIVATE_KEY_PEM")
    if not pem:
        return None
    try:
        return serialization.load_pem_private_key(
            pem.encode("utf-8"),
            password=None,
        )
    except Exception as e:
        logging.error(f"Invalid RSA key: {e}")
        return None


def _sign_bytes(private_key, data: bytes) -> str:
    return private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    ).hex()


def build_manifest_and_sign(
    firms_path: Path,
    dataset_path: Path,
    manifest_output_path: Path,
):
    now_iso = datetime.now(timezone.utc).isoformat()

    dist = []
    for p in [firms_path, dataset_path]:
        if not p.exists():
            logging.warning(f"Missing file for manifest: {p}")
            continue
        dist.append(
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
        "name": "VeriTrust Tier-0 SRA Manifest",
        "dateModified": now_iso,
        "distribution": dist,
    }

    canonical_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    key = _load_private_key()
    if key:
        manifest["vt:signature"] = {
            "algorithm": "RSA-SHA256",
            "value": _sign_bytes(key, canonical_bytes),
        }

    tmp = manifest_output_path.with_suffix(".tmp")

    try:
        manifest_output_path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        tmp.replace(manifest_output_path)
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        raise
