import pytest
import datetime
from unittest.mock import patch, call

from c2corg_api.models._core import OUTING_TYPE

from c2corg_api.legacy.models.cache_version import CacheVersion
from c2corg_api.tests.legacy.views import BaseTestRest

from c2corg_api.legacy.models.association import Association
from c2corg_api.legacy.models.document import DocumentGeometry, DocumentLocale
from c2corg_api.legacy.models.document_topic import DocumentTopic
from c2corg_api.legacy.models.outing import Outing, OutingLocale
from c2corg_api.legacy.models.user_profile import USERPROFILE_TYPE
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.legacy.models.image import Image

from requests.exceptions import ConnectionError


class TestForumTopicRest(BaseTestRest):
    def _add_test_data(self):
        self.locale_en = WaypointLocale(lang="en", title="Mont Granier", description="...", access="yep")
        self.waypoint = Waypoint(waypoint_type="summit", elevation=2203, locales=[self.locale_en])
        self.waypoint.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.waypoint)

        self.waypoint_with_topic = Waypoint(waypoint_type="summit", elevation=2203)
        document_topic = DocumentTopic(topic_id=1)
        self.locale_en_with_topic = WaypointLocale(
            lang="en", title="Mont Granier", description="...", access="yep", document_topic=document_topic
        )
        self.waypoint_with_topic.locales.append(self.locale_en_with_topic)
        self.waypoint_with_topic.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.waypoint_with_topic)

        self.image = Image(filename="image.jpg", activities=["paragliding"], height=1500, image_type="collaborative")
        self.image_locale_en = DocumentLocale(lang="en", title="", description="")
        self.image.locales.append(self.image_locale_en)
        self.image.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.image)

        self.outing = Outing(
            activities=["skitouring"],
            date_start=datetime.date(2016, 1, 1),
            date_end=datetime.date(2016, 1, 1),
            locales=[OutingLocale(lang="en", title="Mont Granier / skitouring")],
        )
        self.session_add(self.outing)
        self.session.flush()

        for user_id in (self.global_userids["contributor"], self.global_userids["contributor2"]):
            self.session_add(
                Association(
                    parent_document_id=user_id,
                    parent_document_type=USERPROFILE_TYPE,
                    child_document_id=self.outing.document_id,
                    child_document_type=OUTING_TYPE,
                )
            )

        self.session.flush()

    def setup_method(self):
        BaseTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    @patch("pydiscourse.client.DiscourseClient.create_post", return_value={"topic_id": 10})
    def test_post_without_title(self, create_post_mock):
        """Test topic link content for documents without title"""
        self.post_json_with_contributor(
            "/forum/topics",
            {"document_id": self.image.document_id, "lang": "en"},
            status=200,
        )

        referer = f"https://www.camptocamp.org/images/{self.image.document_id}/en"
        create_post_mock.assert_called_with(
            f'<a href="{referer}">/images/{self.image.document_id}/en</a>',
            title=f"{self.image.document_id}_en",
            category=666,
        )

    @patch("pydiscourse.client.DiscourseClient.create_post", return_value={"topic_id": 10})
    def test_post_success(self, create_post_mock):
        version = self.locale_en.version
        json = self.post_json_with_contributor(
            "/forum/topics", {"document_id": self.waypoint.document_id, "lang": "en"}, status=200
        )

        doc = self.get(f"/v7/document/{self.waypoint.document_id}").json["document"]

        assert doc["metadata"]["topics"]["en"] == 10
