import json
import requests
from c2corg_api.legacy.converter import convert_from_legacy_doc  # , convert_to_legacy_doc
from c2corg_api.schemas import schema_validator


def check(document_id, document_type):
    legacy_doc = requests.get(f"https://api.camptocamp.org/{document_type}s/{document_id}", timeout=10).json()

    v7_doc = convert_from_legacy_doc(legacy_doc, document_type, {})

    try:
        schema_validator.validate(v7_doc["data"], f"{document_type}.json")
    except:
        print(json.dumps(v7_doc["data"], indent=2))
        raise

    # v6_doc = convert_to_legacy_doc(v7_doc)


check(14478, "area")
check(1481720, "article")
check(1481547, "book")
check(1482727, "image")
check(213355, "route")
check(58034, "route")
check(53884, "route")
