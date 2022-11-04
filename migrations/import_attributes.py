#!/usr/bin/env python3

import json


def main():
    with open("../v6_api/c2corg_api/models/common/attributes.py", "r", encoding="utf-8") as f:
        code = "".join(f.readlines())

    exec(code.encode("utf8"))  # pylint: disable=exec-used

    result = dict(locals())
    result.pop("code")
    result.pop("f")

    for name, value in result.items():
        with open(f"c2corg_api/schemas/attributes/{name}.json", mode="w", encoding="utf-8") as f:
            json.dump({"enum": value}, f, indent=2)


main()
