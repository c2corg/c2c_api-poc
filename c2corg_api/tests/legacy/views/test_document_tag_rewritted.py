import pytest
from c2corg_api.legacy.models.route import Route, RouteLocale, ROUTE_TYPE
from c2corg_api.legacy.models.document_tag import DocumentTag, DocumentTagLog
from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.views.document_tag import get_tag_relation


def has_tagged(user_id, document_id):
    return get_tag_relation(user_id, document_id) is not None


class BaseDocumentTagTest(BaseTestRest):
    def setup_method(self):
        super().setup_method()

        self.contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        self.contributor2 = self.query_get(User, user_id=self.global_userids["contributor2"])

        self.route1 = Route(activities=["skitouring"], locales=[RouteLocale(lang="en", title="Route1")])
        self.session_add(self.route1)
        self.route2 = Route(activities=["skitouring"], locales=[RouteLocale(lang="en", title="Route2")])
        self.session_add(self.route2)
        self.route3 = Route(activities=["hiking"], locales=[RouteLocale(lang="en", title="Route3")])
        self.session_add(self.route3)
        self.session.flush()

        self.session_add(
            DocumentTag(user_id=self.contributor2.id, document_id=self.route2.document_id, document_type=ROUTE_TYPE)
        )
        self.session.flush()


class TestDocumentTagRest(BaseDocumentTagTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/tags/add"

    def test_tag(self):
        request_body = {"document_id": self.route1.document_id}

        self.post_json_with_contributor(self._prefix, request_body, status=200, username="contributor")

        assert has_tagged(self.contributor.id, self.route1.document_id) is True


class TestDocumentUntagRest(BaseDocumentTagTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/tags/remove"

    def test_untag(self):
        request_body = {"document_id": self.route2.document_id}

        assert has_tagged(self.contributor2.id, self.route2.document_id) is True

        self.post_json_with_contributor(self._prefix, request_body, status=200, username="contributor2")

        assert has_tagged(self.contributor2.id, self.route2.document_id) is False
