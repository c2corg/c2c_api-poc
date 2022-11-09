import json
import requests

import pytest

from c2corg_api.legacy.converter import convert_from_legacy_doc  # , convert_to_legacy_doc
from c2corg_api.schemas import schema_validator


docs = [
    ("area", 14478),
    ("article", 1481720),
    ("book", 1481547),
    ("image", 1482727),
    ("route", 213355),
    ("route", 58034),
    ("route", 53884),
    ("route", 53896),
    ("route", 670775),
    ("route", 50892),
    ("xreport", 1449556),
]


@pytest.mark.parametrize("document_type, document_id", docs)
def test_converter(document_id, document_type):
    legacy_doc = requests.get(f"https://api.camptocamp.org/{document_type}s/{document_id}", timeout=10).json()

    v7_doc = convert_from_legacy_doc(legacy_doc, document_type, {})

    try:
        schema_validator.validate(v7_doc["data"], f"{document_type}.json")
    except:
        print(json.dumps(v7_doc["data"], indent=2))
        raise

    # v6_doc = convert_to_legacy_doc(v7_doc)
