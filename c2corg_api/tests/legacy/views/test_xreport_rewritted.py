import pytest
import datetime

from c2corg_api.legacy.caching import cache_document_version
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.association import AssociationLog, Association
from c2corg_api.legacy.models.cache_version import get_cache_key
from c2corg_api.legacy.models.document import DocumentLocale, DocumentGeometry
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.image import Image
from c2corg_api.legacy.models.outing import Outing
from c2corg_api.legacy.models.user_profile import USERPROFILE_TYPE
from c2corg_api.legacy.models.xreport import ArchiveXreport, Xreport, XREPORT_TYPE, ArchiveXreportLocale, XreportLocale
from c2corg_api.legacy.models.route import Route
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.tests.legacy.search import reset_search_index
from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from c2corg_api.legacy.views.document import DocumentRest
from c2corg_api.models.common.attributes import quality_types

# from dogpile.cache.api import NO_VALUE


class TestXreportRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/xreports", XREPORT_TYPE, Xreport, ArchiveXreport, ArchiveXreportLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_post_success(self):
        body = {
            "document_id": 123456,
            "version": 567890,
            "event_activity": "skitouring",
            "event_type": "stone_ice_fall",
            "nb_participants": 5,
            "nb_outings": "nb_outings9",
            "autonomy": "autonomous",
            "activity_rate": "activity_rate_m2",
            "supervision": "professional_supervision",
            "qualification": "federal_trainer",
            "associations": {
                "images": [{"document_id": self.image2.document_id}],
                "articles": [{"document_id": self.article2.document_id}],
            },
            "geometry": {
                "version": 1,
                "document_id": self.waypoint2.document_id,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "locales": [{"title": "Lac d'Annecy", "lang": "en"}],
        }
        body, doc = self.post_success(body, user="moderator", validate_with_auth=True)
        version = doc.versions[0]

        archive_xreport = version.document_archive
        assert archive_xreport.event_activity == "skitouring"
        assert archive_xreport.event_type == "stone_ice_fall"
        assert archive_xreport.nb_participants == 5
        assert hasattr(archive_xreport, "nb_outings") is False
        # assert 'nb_outings' not in archive_xreport
        assert archive_xreport.autonomy == "autonomous"
        assert archive_xreport.activity_rate == "activity_rate_m2"
        assert archive_xreport.supervision == "professional_supervision"
        assert archive_xreport.qualification == "federal_trainer"

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Lac d'Annecy"

        # check if geometry is stored in database afterwards
        assert doc.geometry is not None

    # def test_post_as_contributor_and_get_as_author(self):
    #     body_post = {
    #         "document_id": 111,
    #         "version": 1,
    #         "event_activity": "skitouring",
    #         "event_type": "stone_ice_fall",
    #         "nb_participants": 666,
    #         "nb_impacted": 666,
    #         "locales": [
    #             # {'title': 'Lac d\'Annecy', 'lang': 'fr'},
    #             {"title": "Lac d'Annecy", "lang": "en"}
    #         ],
    #     }

    #     # create document (POST uses GET schema inside validation)
    #     body_post, doc = self.post_success(body_post, user="contributor")

    #     # the contributor is successfully set as author in DB
    #     user_id = self.global_userids["contributor"]
    #     version = doc.versions[0]
    #     meta_data = version.history_metadata
    #     assert meta_data.user_id == user_id

    #     # authorized contributor can see personal data in the xreport
    #     body = self.get_custom(doc, user="contributor", ignore_checks=True)
    #     assert "xreport" not in body

    #     assert "author_status" in body
    #     assert "activity_rate" in body
    #     assert "age" in body
    #     assert "gender" in body
    #     assert "previous_injuries" in body
    #     assert "autonomy" in body

    # def test_post_anonymous(self):
    #     self.app.app.registry.anonymous_user_id = self.global_userids["moderator"]
    #     body_post = {
    #         "document_id": 111,
    #         "version": 1,
    #         "event_activity": "skitouring",
    #         "event_type": "stone_ice_fall",
    #         "nb_participants": 666,
    #         "nb_impacted": 666,
    #         "locales": [{"title": "Lac d'Annecy", "lang": "en"}],
    #         "anonymous": True,
    #     }

    #     body_post, doc = self.post_success(body_post, user="contributor")

    #     # Check that the contributor is not set as author
    #     user_id = self.global_userids["contributor"]
    #     version = doc.versions[0]
    #     meta_data = version.history_metadata
    #     assert meta_data.user_id != user_id
    #     assert meta_data.user_id == self.global_userids["moderator"]

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.xreport1.document_id,
                "version": self.xreport1.version,
                "quality": quality_types[1],
                "event_activity": "skitouring",
                "event_type": "stone_ice_fall",
                "nb_participants": 333,
                "nb_impacted": 666,
                "age": 50,
                "rescue": False,
                "associations": {
                    "images": [{"document_id": self.image2.document_id}],
                    "articles": [{"document_id": self.article2.document_id}],
                },
                "geometry": {"geom": '{"type": "Point", "coordinates": [635956, 5723604]}'},
                "locales": [
                    {
                        "lang": "en",
                        "title": "New title",
                        "place": "some NEW place descrip. in english",
                        "version": self.locale_en.version,
                    }
                ],
            },
        }
        (body, xreport1) = self.put_success_all(body, self.xreport1, user="moderator", cache_version=3)

        assert xreport1.event_activity == "skitouring"
        locale_en = xreport1.get_locale("en")
        assert locale_en.title == "New title"

        # version with lang 'en'
        versions = xreport1.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "New title"
        assert archive_locale.place == "some NEW place descrip. in english"

        archive_document_en = version_en.document_archive
        assert archive_document_en.event_activity == "skitouring"
        assert archive_document_en.event_type == "stone_ice_fall"
        assert archive_document_en.nb_participants == 333
        assert archive_document_en.nb_impacted == 666

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Lac d'Annecy"

        # check if geometry is stored in database afterwards
        assert xreport1.geometry is not None

    # def test_put_as_associated_user(self):
    #     body = {
    #         "message": "Update",
    #         "document": {
    #             "document_id": self.xreport1.document_id,
    #             "version": self.xreport1.version,
    #             "quality": quality_types[1],
    #             "event_activity": "alpine_climbing",  # changed
    #             "event_type": "crevasse_fall",  # changed
    #             "age": 25,  # PERSONAL DATA CHANGED
    #             "locales": [{"lang": "en", "title": "Renamed title by assoc. user", "version": self.locale_en.version}],
    #             "associations": {  # added associations
    #                 "articles": [{"document_id": self.article2.document_id}],
    #                 "routes": [{"document_id": self.route3.document_id}],
    #             },
    #         },
    #     }

    #     (body, xreport1) = self.put_success_all(body, self.xreport1, user="contributor3", cache_version=3)

    #     # version with lang 'en'
    #     versions = xreport1.versions
    #     version_en = self.get_latest_version("en", versions)
    #     archive_locale = version_en.document_locales_archive
    #     assert archive_locale.title == "Renamed title by assoc. user"

    #     archive_document_en = version_en.document_archive
    #     assert archive_document_en.event_activity == "alpine_climbing"
    #     assert archive_document_en.event_type == "crevasse_fall"
    #     assert archive_document_en.age == 25

    def _add_test_data(self):
        self.xreport1 = Xreport(
            event_activity="skitouring", event_type="stone_ice_fall", date=datetime.date(2020, 1, 1)
        )
        self.locale_en = XreportLocale(lang="en", title="Lac d'Annecy", place="some place descrip. in english")
        self.locale_fr = XreportLocale(lang="fr", title="Lac d'Annecy", place="some place descrip. in french")

        self.xreport1.locales.append(self.locale_en)
        self.xreport1.locales.append(self.locale_fr)

        self.session_add(self.xreport1)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.xreport1, user_id)
        self.xreport1_version = self.session_query_first(DocumentVersion, document_id=self.xreport1.document_id)

        user_id3 = self.global_userids["contributor3"]
        self._add_association(
            Association(
                parent_document_id=user_id3,
                parent_document_type=USERPROFILE_TYPE,
                child_document_id=self.xreport1.document_id,
                child_document_type=XREPORT_TYPE,
            ),
            user_id,
        )

        self.xreport2 = Xreport(
            event_activity="skitouring", event_type="avalanche", nb_participants=5, date=datetime.date(2021, 1, 1)
        )
        self.session_add(self.xreport2)
        self.xreport3 = Xreport(
            event_activity="skitouring", event_type="avalanche", nb_participants=5, date=datetime.date(2018, 1, 1)
        )
        self.session_add(self.xreport3)
        self.xreport4 = Xreport(
            event_activity="skitouring", event_type="avalanche", nb_participants=5, nb_impacted=5, age=50
        )
        self.xreport4.locales.append(DocumentLocale(lang="en", title="Lac d'Annecy"))
        self.xreport4.locales.append(DocumentLocale(lang="fr", title="Lac d'Annecy"))
        self.session_add(self.xreport4)

        self.article2 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article2)
        self.session.flush()

        self.image2 = Image(filename="image2.jpg", activities=["paragliding"], height=1500)
        self.session_add(self.image2)
        self.session.flush()

        self.waypoint1 = Waypoint(waypoint_type="summit", elevation=2203)
        self.session_add(self.waypoint1)
        self.waypoint2 = Waypoint(
            waypoint_type="climbing_outdoor",
            elevation=2,
            rock_types=[],
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
        )
        self.session_add(self.waypoint2)
        self.session.flush()

        self.outing3 = Outing(
            activities=["skitouring"], date_start=datetime.date(2016, 2, 1), date_end=datetime.date(2016, 2, 2)
        )
        self.session_add(self.outing3)
        self.route3 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=500,
            height_diff_down=500,
            durations="1",
        )
        self.session_add(self.route3)
        self.session.flush()

        self._add_association(Association.create(parent_document=self.outing3, child_document=self.xreport1), user_id)
        self._add_association(Association.create(parent_document=self.route3, child_document=self.xreport1), user_id)
        self.session.flush()
