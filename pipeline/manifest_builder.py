import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding



def _file_sha256(path: Path) -> str:
    """Compute SHA‑256 hash of a file safely."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()




def _try_load_private_key():
    """
    Load RSA private key from environment variable VT_PRIVATE_KEY_PEM.
    If missing or invalid → return None (unsigned manifest is allowed).
    """
    pem = os.getenv("VT_PRIVATE_KEY_PEM")

    if not pem:
        logging.warning("VT_PRIVATE_KEY_PEM not set — manifest will NOT be signed.")
        return None

    try:
        return serialization.load_pem_private_key(
            pem.encode("utf-8"),
            password=None,
        )
    except Exception as e:
        logging.error("Failed to load RSA private key: %s", e)
        return None




def _sign_bytes(private_key, data: bytes) -> str:
    """Sign bytes with RSA private key and return the hex signature."""
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return signature.hex()




def build_manifest_and_sign(
    firms_path: Path,
    dataset_path: Path,
    manifest_output_path: Path,
) -> None:
    """
    Build Tier‑0 manifest.jsonld.
    - Lists firms.jsonld & dataset.jsonld with SHA‑256 + size
    - Adds RSA-SHA256 signature IF private key is provided
    """

    now_iso = datetime.now(timezone.utc).isoformat()

  
    files_info = []

    for p in [firms_path, dataset_path]:
        if not p.exists():
            logging.warning("Manifest builder: missing file → %s", p)
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
        "name": "VeriTrust Tier-0 SRA Manifest",
        "dateModified": now_iso,
        "distribution": files_info,
    }


    # Optional signature
   
    private_key = _try_load_private_key()

    if private_key:
        compact_bytes = json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        signature_hex = _sign_bytes(private_key, compact_bytes)

        manifest["vt:signature"] = {
            "algorithm": "RSA-SHA256",
            "value": signature_hex,
        }

   
    try:
        manifest_output_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_output_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        logging.info("✔ manifest.jsonld written → %s", manifest_output_path)

    except Exception as e:
        logging.error("❌ Failed to write manifest.jsonld: %s", e)
        raise
