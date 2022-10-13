from flask_camp.client import ClientInterface
from c2corg_api.app import create_app


class BaseTestRest(ClientInterface):

    client = None

    @classmethod
    def setup_class(cls):
        cls.app, cls.api = create_app(TESTING=True)

    def setup_method(self):
        with self.app.app_context():
            self.api.database.create_all()

        with self.app.test_client() as client:
            self.client = client

    def teardown_method(self):
        with self.app.app_context():
            self.api.database.drop_all()

        self.api.memory_cache.flushall()

    @staticmethod
    def _convert_kwargs(kwargs):
        """convert request argument to flask test client argument"""
        kwargs["query_string"] = kwargs.pop("params", None)

    def get(self, url, **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.get(url, **kwargs)
        self.assert_status_code(r, expected_status)

        return r

    def post(self, url, **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.post(url, **kwargs)
        self.assert_status_code(r, expected_status)

        return r

    def put(self, url, **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.put(url, **kwargs)
        self.assert_status_code(r, expected_status)

        return r

    def delete(self, url, **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.delete(url, **kwargs)
        self.assert_status_code(r, expected_status)

        return r

    @staticmethod
    def assert_status_code(response, expected_status):
        if expected_status is None:
            expected_status = [200]
        elif isinstance(expected_status, int):
            expected_status = [expected_status]

        assert (
            response.status_code in expected_status
        ), f"Status error: {response.status_code} i/o {expected_status}\n{response.data}"
