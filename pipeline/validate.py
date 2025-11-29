
"""

Validation is now exclusively handled by Pydantic models in:
    - normalize.py (initial shaping)
    - jsonld_builder.py (strict Pydantic validation)

This stub is kept ONLY to avoid breaking imports.
"""

import logging
from typing import List, Tuple


def validate_records(firms: List[dict], offices: List[dict]) -> Tuple[List[dict], List[dict]]:
    logging.warning("validate_records() is deprecated — returning input unchanged.")
    return firms, offices
