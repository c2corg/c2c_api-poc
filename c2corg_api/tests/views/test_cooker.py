from c2corg_api.tests.conftest import BaseTestClass


class TestCookerRest(BaseTestClass):
    def test_get(self):
        markdowns = {"lang": "fr", "description": "**strong emphasis** and *emphasis*"}

        response = self.post("/cooker", json=markdowns, status=200)

        htmls = response.json

        # lang is not a markdown field, it must be untouched
        assert markdowns["lang"] == htmls["lang"]
        assert markdowns["description"] != htmls["description"]
