import pytest
from c2corg_api.legacy.models.document import Document, DocumentGeometry
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.views.document import DocumentRest


class BaseProtectTest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        contributor_id = self.global_userids["contributor"]

        self.waypoint = Waypoint(waypoint_type="summit", elevation=2203)

        self.locale = WaypointLocale(lang="en", title="Mont Granier", description="...")
        self.waypoint.locales.append(self.locale)

        self.waypoint.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.waypoint)
        self.session.flush()

        DocumentRest.create_new_version(self.waypoint, contributor_id)

        self.waypoint2 = Waypoint(protected=True, waypoint_type="summit", elevation=2203)

        self.locale2 = WaypointLocale(lang="en", title="Mont Granier2", description="...")
        self.waypoint2.locales.append(self.locale2)

        self.waypoint2.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.waypoint2)
        self.session.flush()

        DocumentRest.create_new_version(self.waypoint2, contributor_id)

        self.session.flush()

    def is_protected(self, document_id):
        document = self.query_get(Document, document_id=document_id)
        self.session_refresh(document)
        return document.protected


class TestDocumentProtectRest(BaseProtectTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/documents/protect"

    def test_protect_unauthorized(self):
        self.app_post_json(self._prefix, {}, status=403)

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, {}, headers=headers, status=403)

    def test_protect(self):
        request_body = {"document_id": self.waypoint.document_id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_protected(self.waypoint.document_id) is True

    def test_protect_already_protected_user(self):
        """Test that protecting an already protected document
        does not raise an error.
        """
        request_body = {"document_id": self.waypoint2.document_id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_protected(self.waypoint2.document_id) is True

    def test_protected_invalid_document_id(self):
        request_body = {"document_id": -1}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=400, headers=headers)


class TestDocumentUnprotectRest(BaseProtectTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/documents/unprotect"

    def test_unprotect_unauthorized(self):
        self.app_post_json(self._prefix, {}, status=403)

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, {}, headers=headers, status=403)

    def test_unprotect(self):
        request_body = {"document_id": self.waypoint2.document_id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_protected(self.waypoint2.document_id) is False

    def test_unprotect_already_unprotected_user(self):
        """Test that unprotecting an already unprotected document
        does not raise an error.
        """
        request_body = {"document_id": self.waypoint.document_id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_protected(self.waypoint.document_id) is False

    def test_protected_invalid_document_id(self):
        request_body = {"document_id": -1}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=400, headers=headers)
