from flask_camp.client import ClientInterface
from flask_camp.models import User
from sqlalchemy import select

from c2corg_api.app import create_app, before_user_creation, ProfilePageLink
from c2corg_api.legacy.search import search_documents
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.search import search


class BaseTestRest(ClientInterface):

    client = None
    global_userids = {}
    global_passwords = {}

    @classmethod
    def setup_class(cls):
        cls.app, cls.api = create_app(TESTING=True, SECRET_KEY="not secret")

    def setup_method(self):

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.session = self.api.database.session()

        self.api.database.create_all()
        self._add_global_test_data()

        self.client = self.app.test_client()

    def teardown_method(self):

        self.app_context.pop()

        with self.app.app_context():
            self.api.database.drop_all()

        self.api.memory_cache.flushall()

    def _add_global_test_data(self):
        self._add_user("contributor", "super pass")
        self._add_user("moderator", "super pass")

    def _add_user(self, name, password):
        user = User(name=name)
        user.set_password(password)
        user.set_email(f"{name}@camptocamp.org")
        user.validate_email(user._email_token)

        self.api.database.session.add(user)

        before_user_creation(user, body={})

        self.api.database.session.flush()

        self.global_userids[user.name] = user.id
        self.global_passwords[user.name] = password

    @staticmethod
    def _convert_kwargs(kwargs):
        """convert request argument to flask test client argument"""
        kwargs["query_string"] = kwargs.pop("params", None)

    def get(self, url, prefix="/v7", **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.get(f"{prefix}{url}", **kwargs)
        self.assert_status_code(r, expected_status)

        return r

    def post(self, url, prefix="/v7", **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        try:
            r = self.client.post(f"{prefix}{url}", **kwargs)
        except:
            if expected_status == 500:
                return None
            raise

        self.assert_status_code(r, expected_status)

        return r

    def put(self, url, prefix="/v7", **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        try:
            r = self.client.put(f"{prefix}{url}", **kwargs)
        except:
            if expected_status == 500:
                return None
            raise

        self.assert_status_code(r, expected_status)

        return r

    def delete(self, url, prefix="/v7", **kwargs):
        expected_status = kwargs.pop("status", 200)
        self._convert_kwargs(kwargs)

        r = self.client.delete(f"{prefix}{url}", **kwargs)
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

    def post_json_with_token(self, url, token, **kwargs):
        return self.app_send_json("post", url, {}, **kwargs)

    def app_post_json(self, url, json, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, prefix="", json=json, **kwargs)

    def query_get(self, klass, **kwargs):
        parameter_name, parameter_value = list(kwargs.items())[0]

        if klass is LegacyUser:
            if parameter_name == "user_id":
                query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == parameter_value)
                result = self.session.execute(query)
                user_id = list(result)[0][0]

                user = self.session.query(User).get(user_id)
                return LegacyUser.from_user(user)
            elif parameter_name == "username":
                user = self.session.query(User).filter_by(User.name == parameter_value).first()
                return LegacyUser.from_user(user)
            else:
                raise TypeError("TODO...")

        if klass is UserProfile:
            return UserProfile(parameter_value)

        raise TypeError("TODO...")

    def extract_nonce(self, _send_mail, key):
        message = _send_mail.call_args_list[0][0][0]
        body = message.body
        token = body.split("=")[1]
        return token

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

    def search_document(self, document_type, id=None, index=None, ignore=None):

        document_ids = search(document_type=document_type, id=id)

        if len(document_ids) == 0:
            if ignore == 404:
                return None
            else:
                raise Exception()

        document_as_dict = self.api.get_cooked_document(document_ids[0])
        data = document_as_dict["data"]

        return {"doc_type": document_as_dict["data"].get("type"), "title_fr": data["locales"]["fr"]["title"]}

    def sync_es(self):
        pass

    @property
    def settings(self):
        return self.app.config
