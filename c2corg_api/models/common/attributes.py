import json

with open("c2corg_api/schemas/attributes/quality_types.json", encoding="utf-8") as f:
    quality_types = json.load(f)["enum"]

with open("c2corg_api/schemas/attributes/default_langs.json", encoding="utf-8") as f:
    default_langs = json.load(f)["enum"]
