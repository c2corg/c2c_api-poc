from flask_camp.client import ClientInterface
from flask_camp.models import User
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from c2corg_api.app import create_app, before_user_creation, ProfilePageLink
from c2corg_api.models.legacy.user import User as LegacyUser
from c2corg_api.models.legacy.user_profile import UserProfile


class BaseTestRest(ClientInterface):

    settings = None  # TODO ?
    client = None

    @classmethod
    def setup_class(cls):

        cls.app, cls.api = create_app(TESTING=True)
        cls.Session = sessionmaker()

    def setup_method(self):
        with self.app.app_context():
            self.api.database.create_all()

            self.connection = self.api.database.engine.connect()
            self.session = self.Session(bind=self.connection)

            self._add_global_test_data()

        with self.app.test_client() as client:
            self.client = client

    def teardown_method(self):

        self.session.close()
        self.connection.close()

        with self.app.app_context():
            self.api.database.drop_all()

        self.api.memory_cache.flushall()

    def _add_global_test_data(self):
        contributor = User(name="contributor")
        contributor.set_password("super pass")
        contributor.set_email("contributor@camptocamp.org")

        self.api.database.session.add(contributor)

        before_user_creation(contributor, body={})

        self.api.database.session.commit()

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

    ######### dedicated function for legacy tests

    def app_post_json(self, url, json, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, json=json, **kwargs)

    def query_get(self, klass, **kwargs):
        parameter_name, parameter_value = list(kwargs.items())[0]

        if klass is LegacyUser:
            query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == parameter_value)
            with self.app.app_context():
                result = self.api.database.session.execute(query)
                user_id = list(result)[0][0]

            user = self.session.query(User).get(user_id)
            return LegacyUser.from_user(user)

        if klass is UserProfile:
            with self.app.app_context():
                return UserProfile(parameter_value)

        raise TypeError("TODO...")

    def extract_nonce(self, _send_mail, key):
        return _send_mail.call_args_list[0][0][1]

    def expunge(self, item):
        if isinstance(item, UserProfile):
            return
            # self.session.expunge(item._user)
        elif isinstance(item, LegacyUser):
            self.session.expunge(item._user)
        else:
            self.session.expunge(item)

    def assertErrorsContain(self, body, error_name):
        assert body["status"] != "ok"
