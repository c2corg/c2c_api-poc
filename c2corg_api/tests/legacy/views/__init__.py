from copy import deepcopy
from dateutil import parser as datetime_parser
import json
from os import sync

from flask_camp.models import User, Document, DocumentVersion
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from c2corg_api.hooks import before_validate_user, before_create_user
from c2corg_api.models.userprofile import UserProfile
from c2corg_api.models import MAP_TYPE, USERPROFILE_TYPE, models
from c2corg_api.legacy.models.association import Association as LegacyAssociation
from c2corg_api.legacy.models.document import DocumentLocale as LegacyDocumentLocale
from c2corg_api.legacy.models.document_tag import (
    DocumentTag as LegacyDocumentTag,
    DocumentTagLog as LegacyDocumentTagLog,
)
from c2corg_api.legacy.models.document_history import DocumentVersion as LegacyDocumentVersion
from c2corg_api.legacy.models.area import Area as LegacyArea
from c2corg_api.legacy.models.article import Article as LegacyArticle
from c2corg_api.legacy.models.book import Book as LegacyBook
from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.legacy.models.feed import DocumentChange as LegacyDocumentChange
from c2corg_api.legacy.models.image import Image as LegacyImage
from c2corg_api.legacy.models.outing import Outing as LegacyOuting
from c2corg_api.legacy.models.route import Route as LegacyRoute
from c2corg_api.legacy.models.topo_map import TopoMap as LegacyTopoMap
from c2corg_api.legacy.models.topo_map_association import TopoMapAssociation
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.user_profile import UserProfile as LegacyUserProfile
from c2corg_api.legacy.models.waypoint import Waypoint as LegacyWaypoint
from c2corg_api.legacy.models.xreport import Xreport as LegacyXreport
from c2corg_api.legacy.search import search_documents
from c2corg_api.schemas import schema_validator
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
        geom = {"type": "Point", "coordinates": [0, 0]}

        self._add_user("robot", "bombproof pass", locale_langs=["en"])
        self._add_user("moderator", "super pass", locale_langs=["en"], roles=["moderator"])
        self._add_user("contributor2", "super pass", locale_langs=["en"])
        self._add_user("contributor3", "poor pass", locale_langs=["en"])
        self._add_user("contributor", "super pass", locale_langs=["en", "fr"], geom=geom)

        self.api.database.session.commit()

    def _add_user(self, name, password, locale_langs, roles=None, geom=None):
        user = User(name=name, data=get_default_data(name), roles=[] if roles is None else roles)
        self.api.database.session.add(user)

        user.set_password(password)
        user.set_email(f"{name}@camptocamp.org")
        self.api.database.session.flush()

        UserProfile().create(user, locale_langs=locale_langs, geom=geom, session=self.session)

        user.validate_email(user._email_token)
        self.api.database.session.flush()
        before_validate_user(user, sync_sso=False)

        self.global_userids[user.name] = user.id
        self.global_passwords[user.name] = password
        self.global_email[user.name] = f"{name}@camptocamp.org"

    ######### dedicated function for legacy tests
    def check_cache_version(self, user_id, cache_version):
        pass

    def add_authorization_header(self, username="contributor"):
        self.optimized_login(username)

        return {}

    def optimized_login(self, user_name):
        if user_name is not None:
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
        result = self.post(url, json=json, status=status).json
        if result["status"] != "ok" and "description" in result:
            result["errors"] = [{"description": result["description"]}]

        return result

    def post_json_with_token(self, url, token, **kwargs):
        return self.app_send_json("post", url, {}, **kwargs)

    def app_post_json(self, url, json, expect_errors=None, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_put_json(self, url, json, **kwargs):
        return self.app_send_json("put", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, json=json, **kwargs)

    def session_add(self, instance):
        legacy_document = (
            LegacyArea,
            LegacyArticle,
            LegacyBook,
            LegacyImage,
            LegacyRoute,
            LegacyTopoMap,
            LegacyOuting,
            LegacyUserProfile,
            LegacyWaypoint,
            LegacyXreport,
        )

        if isinstance(instance, legacy_document):

            self.session.add(instance._document)
            self.session.flush()

            if instance._document.redirects_to is None:
                data = instance._version.data
                document_type = data["type"]
                schema_validator.validate(data, f"{document_type}.json")
                models[document_type].update_document_search_table(
                    instance._document, instance._document.last_version, session=self.session
                )

        elif isinstance(instance, LegacyUser):
            self.session.add(instance._user)
            self.session.flush()
            instance.profile._version.data |= {"user_id": instance.id}
            flag_modified(instance.profile._version, "data")

            search_item = models["profile"].update_document_search_table(
                instance.profile._document, instance.profile._document.last_version, session=self.session
            )

            search_item.user_is_validated = instance.email_validated

            self.session.flush()

        elif isinstance(instance, LegacyDocumentTag):
            self.session.add(instance._tag)
            self.session.flush()
        elif isinstance(instance, TopoMapAssociation):
            instance.propagate_in_documents()
        elif isinstance(instance, LegacyDocumentChange):
            instance.propagate_in_documents()
        elif isinstance(instance, LegacyAssociation):
            instance.propagate_in_documents()
        elif isinstance(instance, LegacyDocumentTagLog):
            pass
        elif instance is None:
            pass
        else:
            raise NotImplementedError(f"Don't know how to add {instance}")

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

        if klass is LegacyArticle:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyArticle(version=doc.last_version)

        if klass is LegacyBook:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyBook(version=doc.last_version)

        if klass is LegacyXreport:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyXreport(version=doc.last_version)

        if klass is LegacyTopoMap:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyTopoMap(version=doc.last_version)

        if klass is LegacyDocument:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyDocument(version=doc.last_version)

        if klass is LegacyArea:
            doc = self.session.query(Document).get(parameter_value)
            return LegacyArea(version=doc.last_version)

        raise NotImplementedError(f"TODO...: {klass}")

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
            self.session.refresh(item._user)
        elif isinstance(item, LegacyDocument):
            self.session.refresh(item._document)
        elif isinstance(item, LegacyDocumentLocale):
            pass
        else:
            raise NotImplementedError(f"Can't refresh {item}")

    def session_query_first(self, klass, document_id):
        if klass is LegacyDocumentVersion:
            return self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).first()

        raise NotImplementedError(f"Can't query {klass}")

    def assertErrorsContain(self, body, error_name, comment=None):
        assert body["status"] != "ok", comment

    def search_document(self, document_type, id=None, user_id=None, index=None, ignore=None):

        document_ids = search(document_type=document_type, id=id, user_id=user_id)

        if len(document_ids) == 0:
            if ignore == 404:
                return None
            else:
                raise Exception()

        document_as_dict = self.api.get_cooked_document(document_ids[0])
        data = document_as_dict["data"]

        result = {"doc_type": document_as_dict["data"].get("type"), "document_id": document_as_dict["id"]}

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

    def assertIsNotNone(self, value):
        assert value is not None

    def assertEqual(self, a, b):
        assert a == b, f"{a} == {b}"

    def assertTrue(self, a):
        assert a is True


class BaseDocumentTestRest(BaseTestRest):
    def set_prefix_and_model(self, prefix, document_type, document_class, archive_class, locale_class):
        self._prefix = prefix
        self._model = document_class
        self._doc_type = document_type

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
        assert locale["lang"] == "fr", locales

        assert "protected" in doc
        assert "type" in doc

        return body

    def get_collection_search(self, params=None, user=None):
        if user:
            self.optimized_login(user)

        response = self.get(self._prefix, params=params, status=200)

        return response.json

    def get_locale(self, lang, locales):
        return next(filter(lambda locale: locale["lang"] == lang, locales), None)

    def get_custom(self, reference, user=None, check_title=True, ignore_checks=False):
        if user:
            self.optimized_login(user)

        response = super().get(self._prefix + "/" + str(reference.document_id), status=200)

        body = response.json
        assert "id" not in body
        assert "type" in body
        assert body.get("document_id") == reference.document_id

        assert body.get("version") is not None

        if body["type"] != "m":  # maps
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
        assert "topic_id" in locale_en, locale_en
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

    def get_version(self, reference, reference_version, user=None):
        self.add_authorization_header(username=user)
        response = self.get(f"{self._prefix}/{reference.document_id}/en/{reference_version.id}", status=200)
        assert response.content_type == "application/json", response.content_type

        body = response.json
        assert "document" in body
        assert "version" in body
        assert "previous_version_id" in body
        assert "next_version_id" in body

        assert "cooked" in body["document"], list(body["document"].keys())
        assert "lang" in body["document"]["cooked"]

        assert body["document"]["cooked"]["lang"] == "en"
        assert body["document"]["document_id"] == reference.document_id
        assert body["version"]["version_id"] == reference_version.id

        version = body["version"]
        written_at = version["written_at"]
        time = datetime_parser.parse(written_at)
        assert time.tzinfo is not None

        return body

    def post_error(self, request_body, user="contributor"):

        self.add_authorization_header(username=user)
        response = self.app_post_json(self._prefix, request_body, status=400)

        body = response.json
        assert body.get("status") == "error"
        body["errors"] = body["description"]  # make legacy test happy
        return body

    def post_missing_title(self, request_body, user="contributor", prefix=""):

        self.add_authorization_header(username=user)
        response = self.app_post_json(self._prefix, request_body, status=400)

        body = response.json
        assert body.get("status") == "error"
        assert "'title' is a required property on instance ['locales']['en']" in body.get("description"), body

        return body

    def post_non_whitelisted_attribute(self, request_body, user="contributor"):
        """`protected` is a non-whitelisted attribute, which is ignored when given in a request."""
        self.add_authorization_header(username=user)
        response = self.app_post_json(self._prefix, request_body, status=200)

        body = response.json
        document_id = body.get("document_id")
        document = self.session.query(Document).get(document_id)
        # the value for `protected` was ignored
        assert document.protected is False
        return (body, document)

    def post_wrong_geom_type(self, request_body):

        self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, status=400)

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("description")
        return errors

    def post_missing_content_type(self, request_body):
        self.add_authorization_header(username="moderator")
        response = self.post(self._prefix, data=json.dumps(request_body), status=415)

        body = response.json
        assert body.get("status") == "error"
        return body

    def put_wrong_document_id(self, request_body, user="contributor"):
        self.app_put_json(self._prefix + "/9999999", request_body, status=403)

        self.add_authorization_header(username=user)
        self.app_put_json(self._prefix + "/9999999", request_body, status=404)

    def put_wrong_ids(self, request_body, id, user="contributor"):
        """The id given in the URL does not equal the document_id in the request body."""
        request_body["document"]["document_id"] = 9999
        self.add_authorization_header(username=user)
        r = self.app_put_json(self._prefix + "/" + str(id), request_body, status=400).json

        assert r["status"] == "error", r
        assert r["description"] == "Id in body does not match id in URI", r

    def put_wrong_version(self, request_body, id, user="contributor"):
        self.app_put_json(self._prefix + "/" + str(id), request_body, status=403)

        self.add_authorization_header(username=user)
        self.app_put_json(self._prefix + "/" + str(id), request_body, status=409)

        # TODO
        # body = response.json
        # self.assertEqual(body["status"], "error")
        # self.assertEqual(body["errors"][0]["name"], "Conflict")

    def put_put_no_document(self, id, user="contributor"):
        request_body = {"message": "..."}
        self.add_authorization_header(username=user)
        r = self.app_put_json(self._prefix + "/" + str(id), request_body, status=400).json

        assert r["status"] == "error"

    def put_success_all(self, request_body, document, user="contributor", check_es=True, cache_version=2):
        document_version = document.version
        self.add_authorization_header(username=user)
        self.app_put_json(f"{self._prefix}/{document.document_id}", request_body, status=200)

        response = self.get(self._prefix + "/" + str(document.document_id), status=200)
        assert response.content_type == "application/json"

        body = response.json
        document_id = body.get("document_id")
        assert body.get("version") != document_version, f'{body.get("version")} vs {document_version}'
        assert body.get("document_id") == document_id

        # check that the document was updated correctly
        self.session.expire_all()
        document = self._model(version=self.session.query(Document).get(document_id).last_version)
        assert len(document.locales) == 2, document.locales
        locale_en = document.get_locale("en")

        # check that a new archive_document was created
        archive_count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        assert archive_count == 2

        # check that new versions were created
        versions = document.versions
        assert len(versions) == 2, versions  # 4 on old model

        return (body, document)

    def put_success_figures_only(self, request_body, document, user="contributor", check_es=True):
        """Test updating a document with changes to the figures only."""

        document_version = document.version
        self.add_authorization_header(username=user)
        self.app_put_json(self._prefix + "/" + str(document.document_id), request_body, status=200)

        response = self.get(self._prefix + "/" + str(document.document_id), status=200)

        body = response.json
        document_id = body.get("document_id")
        assert body.get("version") != document_version, f'{body.get("version")} vs {document_version}'
        assert body.get("document_id") == document_id

        # check that the document was updated correctly
        self.session.expire_all()
        document = self._model(version=self.session.query(Document).get(document_id).last_version)
        assert len(document.locales) == 2, document.locales

        # check that a new archive_document was created
        archive_count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        assert archive_count == 2

        # check that new versions were created
        versions = document.versions
        assert len(versions) == 2, versions  # 4 on old model

        return (body, document)

    def put_success_lang_only(self, request_body, document, user="contributor", check_es=True):
        document_version = document.version
        self.add_authorization_header(username=user)
        self.app_put_json(self._prefix + "/" + str(document.document_id), request_body, status=200)

        response = self.get(self._prefix + "/" + str(document.document_id), status=200)

        body = response.json
        document_id = body.get("document_id")
        # document version changes ! (was not changing in old model)
        assert body.get("version") != document_version, f'{body.get("version")} vs {document_version}'
        assert body.get("document_id") == document_id

        # check that the document was updated correctly
        self.session.expire_all()
        document = self._model(version=self.session.query(Document).get(document_id).last_version)
        assert len(document.locales) == 2, document.locales

        # check that archive_document was created (not the case in old model)
        archive_count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        assert archive_count == 2  # 1 in old model

        # check that new versions were created
        versions = document.versions
        assert len(versions) == 2, versions  # 3 on old model

        return (body, document)

    def put_success_new_lang(self, request_body, document, user="contributor", check_es=True):
        """Test updating a document by adding a new locale."""

        document_version = document.version
        self.add_authorization_header(username=user)
        self.app_put_json(self._prefix + "/" + str(document.document_id), request_body, status=200)

        response = self.get(self._prefix + "/" + str(document.document_id), status=200)

        body = response.json
        document_id = body.get("document_id")
        assert body.get("version") != document_version, f'{body.get("version")} vs {document_version}'
        assert body.get("document_id") == document_id

        # check that the document was updated correctly
        self.session.expire_all()
        document = self._model(version=self.session.query(Document).get(document_id).last_version)
        assert len(document.locales) == 3, document.locales

        # check that a new archive_document was created
        archive_count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        assert archive_count == 2

        return (body, document)

    def assertResultsEqual(self, actual, expected, total):
        message = json.dumps(actual, indent=2)
        expected = sorted(expected)
        actual_ids = sorted(json["document_id"] for json in actual["documents"])
        assert actual_ids == expected, (actual_ids, expected)
        assert actual["total"] == total, message

    def _add_association(self, association, user_id):
        """used for setup"""
        association.propagate_in_documents()

    def post_success(self, request_body, user="contributor", validate_with_auth=False, skip_validation=False):
        self.app_post_json(self._prefix, request_body, status=403)

        self.add_authorization_header(username=user)
        response = self.app_post_json(self._prefix, request_body, status=200)

        body = response.json
        if skip_validation:
            document_id = body.get("document_id")
            response = self.get(self._prefix + "/" + str(document_id), status=200)
            doc = self.query_get(self._model, id=document_id)
            return response.json, doc
        else:
            return self._validate_document(body, validate_with_auth)

    def _validate_document(self, body, headers=None, validate_with_auth=False):
        document_id = body.get("document_id")
        assert document_id is not None

        if validate_with_auth:
            response = self.get(self._prefix + "/" + str(document_id), headers=headers, status=200)
        else:
            self.delete("/v7/user/login")
            response = self.get(self._prefix + "/" + str(document_id), status=200)
        assert response.content_type == "application/json"

        body = response.json
        assert body.get("version") is not None
        assert body.get("protected") == False

        # check that the version was created correctly
        doc = self.query_get(self._model, id=document_id)

        versions = doc.versions
        assert len(versions) == 1
        version = versions[0]

        assert version.comment == "creation", version.comment
        assert version.written_at is not None

        # check updates to the search index
        self.sync_es()
        search_doc = self.search_document(self._doc_type, id=doc.document_id)

        assert search_doc["document_id"] == doc.document_id, search_doc
        assert search_doc["doc_type"] is not None
        assert search_doc["doc_type"] == doc.type

        locale_en = doc.locales[0]

        if isinstance(doc, LegacyRoute):
            title = locale_en.title_prefix + " : " + locale_en.title
            assert search_doc["title_en"] == title
        else:
            assert search_doc["title_en"] == locale_en.title, f"{search_doc['title_en']} vs {locale_en.title}"

        return (body, doc)

    def get_latest_version(self, lang, versions):
        versions[-1]._expected_legacy_lang = lang
        return versions[-1]


def get_locale(locales, lang):
    return next(filter(lambda locale: locale["lang"] == lang, locales), None)
