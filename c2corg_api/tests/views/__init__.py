from flask_camp.client import ClientInterface
from flask_camp.models import User
from sqlalchemy import select

from c2corg_api.app import before_user_creation, ProfilePageLink
from c2corg_api.legacy.search import search_documents
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.search import search
from c2corg_api.tests.conftest import BaseTestClass


class BaseTestRest(BaseTestClass):

    client = None
    global_userids = {}
    global_passwords = {}

    def setup_method(self):
        super().setup_method()

        self._add_global_test_data()

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

    ######### dedicated function for legacy tests

    def get_json_with_contributor(self, url, status=200):
        self.login_user("contributor", self.global_passwords["contributor"])
        return self.get(url, prefix="", status=status).json

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
