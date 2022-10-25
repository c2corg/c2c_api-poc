from os import sync
from flask_camp.models import User
from sqlalchemy import select

from c2corg_api.hooks import on_user_creation, ProfilePageLink, on_user_validation
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.area import Area as LegacyArea
from c2corg_api.legacy.models.user_profile import UserProfile as LegacyUserProfile
from c2corg_api.search import search
from c2corg_api.tests.conftest import BaseTestClass, get_default_ui_preferences


class BaseTestRest(BaseTestClass):

    is_v7_api = False

    client = None
    global_userids = {}
    global_passwords = {}
    global_session_cookies = {}

    def setup_method(self):
        super().setup_method()

        self._add_global_test_data()

    def _add_global_test_data(self):
        self._add_user("contributor", "super pass")
        self._add_user("contributor2", "super pass")
        self._add_user("moderator", "super pass", ["moderator"])

        self.api.database.session.commit()

    def _add_user(self, name, password, roles=None):
        user = User(name=name, ui_preferences=get_default_ui_preferences(name), roles=[] if roles is None else roles)
        self.api.database.session.add(user)

        user.set_password(password)
        user.set_email(f"{name}@camptocamp.org")
        self.api.database.session.flush()

        on_user_creation(user)
        user.validate_email(user._email_token)
        self.api.database.session.flush()

        on_user_validation(user, sync_sso=False)

        self.global_userids[user.name] = user.id
        self.global_passwords[user.name] = password

    ######### dedicated function for legacy tests
    def check_cache_version(self, user_id, cache_version):
        pass

    def add_authorization_header(self, username="contributor"):
        self.optimized_login(username)
        return None

    def optimized_login(self, user_name):
        if user_name not in self.global_session_cookies:
            self.post("/v7/login", json={"name_or_email": user_name, "password": self.global_passwords[user_name]})
            cookies = list(self.client.cookie_jar)
            session_cookie = [cookie for cookie in cookies if cookie.name == "session"][0]
            self.global_session_cookies[user_name] = session_cookie.value
        else:
            self.client.set_cookie("localhost.host", "session", self.global_session_cookies[user_name])

    def get_json_with_contributor(self, url, username="contributor", status=200):
        self.optimized_login(username)
        return self.get(url, status=status).json

    def post_json_with_contributor(self, url, json, username="contributor", status=200):
        self.optimized_login(username)
        return self.post(url, json=json, status=status).json

    def post_json_with_token(self, url, token, **kwargs):
        return self.app_send_json("post", url, {}, **kwargs)

    def app_post_json(self, url, json, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, json=json, **kwargs)

    def session_add(self, instance):
        if isinstance(instance, LegacyArea):
            self.session.add(instance._document)
        elif isinstance(instance, LegacyUserProfile):
            self.session.add(instance._document)
        else:
            raise NotImplementedError()

    def session_add_all(self, instances):
        for instance in instances:
            self.session_add(instance)

    def query_get(self, klass, **kwargs):
        parameter_name, parameter_value = list(kwargs.items())[0]

        if klass is LegacyUser:
            if parameter_name == "user_id":
                user = self.session.query(User).get(parameter_value)
                return LegacyUser.from_user(user)
            elif parameter_name == "username":
                user = self.session.query(User).filter_by(User.name == parameter_value).first()
                return LegacyUser.from_user(user)
            else:
                raise TypeError("TODO...")

        if klass is LegacyUserProfile:
            return LegacyUserProfile.from_document_id(parameter_value)

        raise TypeError("TODO...")

    def extract_nonce(self, _send_mail, key):
        message = _send_mail.call_args_list[0][0][0]
        body = message.body
        token = body.split("=")[1]
        return token

    def expunge(self, item):
        if isinstance(item, LegacyUserProfile):
            return
            # self.session.expunge(item._user)
        elif isinstance(item, LegacyUser):
            self.session.expunge(item._user)
        else:
            self.session.expunge(item)

    def session_refresh(self, item):
        if isinstance(item, LegacyUser):
            self.session.expunge(item._user)
        else:
            raise NotImplementedError()

    def assertErrorsContain(self, body, error_name):
        assert body["status"] != "ok"

    def search_document(self, document_type, id=None, user_id=None, index=None, ignore=None):

        document_ids = search(document_type=document_type, id=id, user_id=user_id)

        if len(document_ids) == 0:
            if ignore == 404:
                return None
            else:
                raise Exception()

        document_as_dict = self.api.get_cooked_document(document_ids[0])
        data = document_as_dict["data"]

        result = {"doc_type": document_as_dict["data"].get("type")}

        for locale in data["locales"]:
            result[f"title_{locale['lang']}"] = locale["title"]

        return result

    def sync_es(self):
        pass

    @property
    def settings(self):
        return self.app.config

    def get_body_error(self, body, string):
        assert string in body["description"], body
        return body["description"]


class BaseDocumentTestRest(BaseTestRest):
    def set_prefix_and_model(self, prefix, document_type, document_class, archive_class, locale_class):
        ...
