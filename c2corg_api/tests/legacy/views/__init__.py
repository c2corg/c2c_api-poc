import json
from os import sync
from flask_camp.models import User
from sqlalchemy import select

from c2corg_api.hooks import on_user_validation
from c2corg_api.models import create_user_profile, ProfilePageLink, USERPROFILE_TYPE
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.area import Area as LegacyArea
from c2corg_api.legacy.models.user_profile import UserProfile as LegacyUserProfile
from c2corg_api.search import search
from c2corg_api.tests.conftest import BaseTestClass, get_default_data


class BaseTestRest(BaseTestClass):

    is_v7_api = False

    client = None
    global_userids = {}
    global_passwords = {}
    global_email = {}
    global_session_cookies = {}

    def setup_method(self):
        super().setup_method()

        self._add_global_test_data()

    def _add_global_test_data(self):
        self._add_user("moderator", "super pass", locale_langs=["en"], roles=["moderator"])
        self._add_user("contributor", "super pass", locale_langs=["en", "fr"])
        self._add_user("contributor2", "super pass", locale_langs=["en"])
        self._add_user("contributor3", "poor pass", locale_langs=["en"])
        self._add_user("robot", "bombproof pass", locale_langs=["en"])

        self.api.database.session.commit()

    def _add_user(self, name, password, locale_langs, roles=None):
        user = User(name=name, data=get_default_data(name), roles=[] if roles is None else roles)
        self.api.database.session.add(user)

        user.set_password(password)
        user.set_email(f"{name}@camptocamp.org")
        self.api.database.session.flush()

        create_user_profile(user, locale_langs=locale_langs)
        user.validate_email(user._email_token)
        self.api.database.session.flush()

        on_user_validation(user, sync_sso=False)

        self.global_userids[user.name] = user.id
        self.global_passwords[user.name] = password
        self.global_email[user.name] = f"{name}@camptocamp.org"

    ######### dedicated function for legacy tests
    def check_cache_version(self, user_id, cache_version):
        pass

    def add_authorization_header(self, username="contributor"):
        self.optimized_login(username)

        return None

    def optimized_login(self, user_name):
        self.put(
            "/v7/user/login",
            json={"name_or_email": self.global_email[user_name], "password": self.global_passwords[user_name]},
        )

    def get_json_with_contributor(self, url, username="contributor", status=200):
        self.optimized_login(username)
        return self.get(url, status=status).json

    def post_json(self, url, json, expect_errors=False, status=200):
        return self.post(url, json=json, status=status)

    def post_json_with_contributor(self, url, json, username="contributor", status=200):
        self.optimized_login(username)
        return self.post(url, json=json, status=status).json

    def post_json_with_token(self, url, token, **kwargs):
        return self.app_send_json("post", url, {}, **kwargs)

    def app_post_json(self, url, json, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_put_json(self, url, json, **kwargs):
        return self.app_send_json("put", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, json=json, **kwargs)

    def session_add(self, instance):
        if isinstance(instance, LegacyArea):
            self.session.add(instance._document)
        elif isinstance(instance, LegacyUserProfile):
            self.session.add(instance._document)
        elif isinstance(instance, LegacyUser):
            self.session.add(instance._user)
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

        if document_as_dict["data"].get("type") == USERPROFILE_TYPE:
            user = User.get(id=document_as_dict["data"]["user_id"])
            for locale in data["locales"].values():
                result[f"title_{locale['lang']}"] = user.name
        else:
            for locale in data["locales"].values():
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
        self._prefix = prefix

    def get_collection(self, params=None, user=None):
        if user:
            self.optimized_login(user)

        return self.get(self._prefix, params=params).json

    def get_collection_lang(self, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(self._prefix, params={"pl": "es"}, status=200)

        body = response.json
        documents = body["documents"]
        assert isinstance(documents, list)

        doc = documents[0]
        locales = doc.get("locales")
        assert len(locales) == 1, locales
        locale = locales[0]
        assert locale["lang"] == "fr"

        assert "protected" in doc
        assert "type" in doc

        return body

    def get_collection_search(self, params=None, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(self._prefix, params=params, status=200)

        return response.json

    def get_custom(self, reference, user=None, check_title=True, ignore_checks=False):
        if user:
            self.optimized_login(user)

        response = super().get(self._prefix + "/" + str(reference.document_id), status=200)

        body = response.json
        assert "id" not in body
        assert "type" in body
        assert body.get("document_id") == reference.document_id

        assert body.get("version") is not None
        assert body.get("associations") is not None

        locales = body.get("locales")
        if ignore_checks is False:
            assert len(locales) == 2

        locale_en = get_locale(locales, "en")

        assert "id" not in locale_en
        assert locale_en.get("version") is not None
        assert locale_en.get("lang") == self.locale_en.lang, locale_en

        if check_title:
            assert locale_en.get("title") == self.locale_en.title

        available_langs = body.get("available_langs")
        if ignore_checks is False:
            assert len(available_langs) == 2

        return body

    def get_cooked(self, reference, user=None):
        body, locale, cooked = self._get_cooked(reference, "en", user)

        assert locale.get("lang") == self.locale_en.lang
        assert locale.get("lang") == "en"
        assert cooked.get("lang") == "en"

        return body

    def get_cooked_with_defaulting(self, reference, user=None):
        body, locale, cooked = self._get_cooked(reference, "it", user)

        assert locale.get("lang") == "fr"
        assert cooked.get("lang") == "fr"

        return body

    def _get_cooked(self, reference, lang, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(f"{self._prefix}/{reference.document_id}", params={"cook": lang}, status=200)

        body = response.json
        assert "cooked" in body
        assert "locales" in body

        locales = body.get("locales")
        cooked = body.get("cooked")

        assert len(locales) == 1

        return body, locales[0], cooked

    def get_lang(self, reference, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(f"{self._prefix}/{reference.document_id}", params={"l": "en"}, status=200)

        body = response.json
        locales = body.get("locales")
        assert len(locales) == 1
        locale_en = locales[0]

        assert locale_en.get("lang") == self.locale_en.lang

        assert "protected" in body
        assert "topic_id" in locale_en
        return body

    def get_new_lang(self, reference, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(f"{self._prefix}/{reference.document_id}", params={"l": "it"}, status=200)

        body = response.json
        locales = body.get("locales")
        assert len(locales) == 0, locales

    def get_404(self, user=None):
        if user:
            self.optimized_login(user)

        self.get(f"{self._prefix}/9999999", status=404)
        self.get(f"{self._prefix}/9999999?l=es", status=404)

    def put_wrong_document_id(self, request_body, user="contributor"):
        response = self.app_put_json(self._prefix + "/9999999", request_body, status=403)

        self.add_authorization_header(username=user)
        response = self.app_put_json(self._prefix + "/9999999", request_body, status=404)

    def assertResultsEqual(self, actual, expected, total):
        message = json.dumps(actual, indent=2)
        expected = sorted(expected)
        actual_ids = sorted(json["document_id"] for json in actual["documents"])
        assert actual_ids == expected, (actual_ids, expected)
        assert actual["total"] == total, message


def get_locale(locales, lang):
    return next(filter(lambda locale: locale["lang"] == lang, locales), None)
