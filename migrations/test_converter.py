from copy import deepcopy
import requests

from c2corg_api.legacy.converter import convert_from_legacy_doc  # , convert_to_legacy_doc
from c2corg_api.schemas import schema_validator


def test_converter(document_id, document_type):
    legacy_doc = requests.get(f"https://api.camptocamp.org/{document_type}s/{document_id}", timeout=10).json()

    v7_doc = convert_from_legacy_doc(deepcopy(legacy_doc), document_type, {})

    try:
        schema_validator.validate(v7_doc["data"], f"{document_type}.json")
    except:  # pylint: disable=bare-except
        print(document_id)
        # with open(f"migrations/documents/{document_id}.json", mode="w", encoding="utf-8") as f:
        #     json.dump(legacy_doc, f, indent=4)

    # v6_doc = convert_to_legacy_doc(v7_doc)


def crawl(document_type):
    params = {"offset": 300, "limit": 100}
    url = f"https://api.camptocamp.org/{document_type}s"

    while True:
        r = requests.get(url, params=params, timeout=10).json()
        print(f"{params['offset']}/{r['total']}")
        documents = r["documents"]

        if len(documents) == 0:
            return

        for document in documents:
            yield document["document_id"]

        params["offset"] += 100


for document_id in crawl("xreport"):
    test_converter(document_id, "xreport")
