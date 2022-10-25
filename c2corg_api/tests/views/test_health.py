from c2corg_api.tests.conftest import BaseTestClass


class TestHealthRest(BaseTestClass):
    def test_get(self):
        self.get("/healthcheck", status=200)
