import json
import requests

import pytest

from c2corg_api.legacy.converter import convert_from_legacy_doc, convert_to_legacy_doc
from c2corg_api.schemas import schema_validator


docs = [
    ("area", (14478,)),
    ("article", (1481720, 1446629, 1440443, 816616, 793856, 747564)),
    ("book", (1481547,)),
    ("image", (1482727,)),
    ("map", (250182,)),
    ("outing", (1482990,)),
    ("route", (213355, 58034, 53884, 53896, 670775, 50892, 50892)),
    ("waypoint", (112210,)),
    ("xreport", (1468590, 808075, 1082547, 1090284, 1413480, 1465817, 1477302, 1449556)),
]


@pytest.mark.parametrize("document_type, document_ids", docs)
def test_converter(document_type, document_ids):
    for document_id in document_ids:
        legacy_doc = requests.get(f"https://api.camptocamp.org/{document_type}s/{document_id}", timeout=10).json()

        v7_doc = convert_from_legacy_doc(legacy_doc, document_type, {})

        try:
            schema_validator.validate(v7_doc["data"], f"{document_type}.json")
        except:
            print(json.dumps(v7_doc["data"], indent=2))
            raise

        convert_to_legacy_doc(v7_doc)
