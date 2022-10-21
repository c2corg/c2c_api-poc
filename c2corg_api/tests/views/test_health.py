import pytest
from c2corg_api.tests.views import BaseTestRest


class TestHealthRest(BaseTestRest):
    def test_get(self):
        r = self.get("/health", status=200, prefix="")

        data = r.json

        assert data["es"] == "ok"
        assert data["redis"] == "ok"
