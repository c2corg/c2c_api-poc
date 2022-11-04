import json

with open("c2corg_api/schemas/attributes/quality_types.json", encoding="utf-8") as f:
    quality_types = json.load(f)["enum"]
