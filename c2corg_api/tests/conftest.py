import json
import logging
import sys

from flask_camp.client import ClientInterface
from flask_camp.models import User
import pytest
from werkzeug.test import TestResponse

from c2corg_api.app import create_app


tested_app, tested_api = create_app(
    TESTING=True, SECRET_KEY="not secret", C2C_DISCOURSE_SSO_SECRET="d836444a9e4084d5b224a60c208dce14"
)


def get_default_data(full_name):
    return {
        "lang": "fr",
        "is_profile_public": False,
        "full_name": full_name,
        "feed": {"areas": [], "langs": [], "followed_only": False, "activities": [], "follow": []},
    }


def pytest_configure(config):
    if config.getoption("-v") > 1:
        logging.getLogger("sqlalchemy").addHandler(logging.StreamHandler(sys.stdout))
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)

    if not config.option.collectonly:

        # clean previous uncleaned state
        # do not perform this on collect, editors that automatically collect tests on file change
        # may break current test session
        with tested_app.app_context():

            # why not using tested_api.database.drop_all()?
            # because in some case, a table is not known by the ORM
            # for instance, run test A that define a custom table, stop it during execution (the table is not removed)
            # then run only test B. Table defined in test A is not known

            sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            rows = tested_api.database.session.execute(sql)
            names = [name for name, in rows]
            if len(names) != 0:
                tested_api.database.session.execute(f"DROP TABLE {','.join(names)} CASCADE;")
                tested_api.database.session.commit()

            tested_api.database.create_all()

        tested_api.memory_cache.flushall()


class BaseTestClass(ClientInterface):

    is_v7_api = True

    client = None

    @classmethod
    def setup_class(cls):
        cls.app, cls.api = tested_app, tested_api

    def setup_method(self):

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.session = self.api.database.session()

        self.api.database.create_all()

        self.client = self.app.test_client()

    def teardown_method(self):

        self.app_context.pop()

        with self.app.app_context():
            self.api.database.drop_all()

        self.api.memory_cache.flushall()

    @staticmethod
    def _convert_kwargs(kwargs):
        """convert request argument to flask test client argument"""
        kwargs["query_string"] = kwargs.pop("params", None)

    def _request(self, method, url, **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        url = f"/v7{url}" if self.is_v7_api else url

        try:
            r = method(url, **kwargs)
        except:
            if expected_status == 500:
                return TestResponse(
                    response='{"status":"error"}',
                    status="500",
                    headers={"content-type": "application/json"},
                    request=None,
                )
            raise

        self.assert_status_code(r, expected_status)

        return r

    def get(self, url, **kwargs):
        return self._request(self.client.get, url, **kwargs)

    def post(self, url, **kwargs):
        return self._request(self.client.post, url, **kwargs)

    def put(self, url, **kwargs):
        return self._request(self.client.put, url, **kwargs)

    def delete(self, url, **kwargs):
        return self._request(self.client.delete, url, **kwargs)

    @staticmethod
    def assert_status_code(response, expected_status):
        if expected_status is None:
            expected_status = [200]
        elif isinstance(expected_status, int):
            expected_status = [expected_status]

        def pretty_message():
            message = f"Status error: {response.status_code} i/o {expected_status} for {response.request.url}"
            try:
                return message + "\n" + json.dumps(response.json, indent=2)
            except:  # pylint: disable=bare-except
                return message + "\n" + str(response.data)

        assert response.status_code in expected_status, pretty_message()

    ### some helpers

    def login_user(self, user, password=None, token=None, **kwargs):
        if password is None and token is None:
            password = "password"

        return super().login_user(user, password=password, token=token, **kwargs)


def _db_add_user(name="name", email=None, password="password", validate_email=True, roles=None):

    instance = User.create(
        name=name,
        password=password,
        email=email if email else f"{name}@site.org",
        data=get_default_data(name),
        roles=roles if isinstance(roles, (list, tuple)) else roles.split(",") if isinstance(roles, str) else [],
    )

    if validate_email:
        instance.validate_email(instance._email_token)

    tested_api.database.session.add(instance)
    tested_api.database.session.commit()

    return instance


@pytest.fixture()
def moderator():
    with tested_app.app_context():
        yield _db_add_user(name="moderator", roles="moderator")


@pytest.fixture()
def user():
    with tested_app.app_context():
        yield _db_add_user(name="user")


@pytest.fixture()
def user_2():
    with tested_app.app_context():
        yield _db_add_user(name="user_2")
