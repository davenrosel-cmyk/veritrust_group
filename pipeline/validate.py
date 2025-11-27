import logging
from typing import List, Tuple

from models import NormalizedFirm, NormalizedOffice


def _str_ok(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate_records(
    firms: List[NormalizedFirm],
    offices: List[NormalizedOffice],
) -> Tuple[List[NormalizedFirm], List[NormalizedOffice]]:

    valid_firms = []
    valid_offices = []

    for f in firms:
        if not _str_ok(f.get("sraId")):
            continue
        if not _str_ok(f.get("name")):
            continue
        if not _str_ok(f.get("regulatoryStatus")):
            continue
        valid_firms.append(f)

    for o in offices:
        if not _str_ok(o.get("officeId")):
            continue
        if not _str_ok(o.get("firmSraId")):
            continue

        addr = o.get("address") or {}
        if not _str_ok(addr.get("streetAddress")):
            continue

        valid_offices.append(o)

    logging.info(
        "Validation → %d/%d firms, %d/%d offices",
        len(valid_firms),
        len(firms),
        len(valid_offices),
        len(offices),
    )

    return valid_firms, valid_offices
