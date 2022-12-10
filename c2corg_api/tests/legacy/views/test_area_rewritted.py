import pytest
import json

from c2corg_api.legacy.models.area import Area, ArchiveArea, AREA_TYPE
from c2corg_api.legacy.models.area_association import AreaAssociation
from c2corg_api.legacy.models.association import Association
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.image import Image
from c2corg_api.legacy.models.route import Route
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.tests.legacy.search import reset_search_index

from c2corg_api.models.common.attributes import quality_types
from shapely.geometry import shape, Polygon

from c2corg_api.legacy.models.document import DocumentGeometry, ArchiveDocumentLocale, DocumentLocale
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest


class TestAreaRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/areas", AREA_TYPE, Area, ArchiveArea, ArchiveDocumentLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def _add_test_data(self):
        self.area1 = Area(area_type="range")

        self.locale_en = DocumentLocale(lang="en", title="Chartreuse")
        self.locale_fr = DocumentLocale(lang="fr", title="Chartreuse")

        self.area1.locales.append(self.locale_en)
        self.area1.locales.append(self.locale_fr)

        self.area1.geometry = DocumentGeometry(
            geom_detail="SRID=3857;POLYGON((668518.249382151 5728802.39591739,668518.249382151 5745465.66808356,689156.247019149 5745465.66808356,689156.247019149 5728802.39591739,668518.249382151 5728802.39591739))"  # noqa
        )

        self.session_add(self.area1)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.area1, user_id)

        self.area1_version = self.session_query_first(DocumentVersion, document_id=self.area1.document_id)

        self.area2 = Area(area_type="range")
        self.session_add(self.area2)
        self.area3 = Area(area_type="range")
        self.session_add(self.area3)
        self.area4 = Area(area_type="admin_limits")
        self.area4.locales.append(DocumentLocale(lang="en", title="Isère"))
        self.area4.locales.append(DocumentLocale(lang="fr", title="Isère"))
        self.session_add(self.area4)

        self.waypoint1 = Waypoint(
            waypoint_type="summit", geometry=DocumentGeometry(geom="SRID=3857;POINT(677461.381691516 5740879.44638645)")
        )
        self.waypoint2 = Waypoint(
            waypoint_type="summit", geometry=DocumentGeometry(geom="SRID=3857;POINT(693666.031687976 5741108.7574713)")
        )
        route_geom = "SRID=3857;LINESTRING(668518 5728802, 668528 5728812)"
        self.route = Route(activities=["skitouring"], geometry=DocumentGeometry(geom_detail=route_geom))

        self.session_add_all([self.waypoint1, self.waypoint2, self.route])
        self.session_add(AreaAssociation(document=self.waypoint2, area=self.area1))

        self.image = Image(
            filename="image.jpg",
            activities=["paragliding"],
            height=1500,
            image_type="collaborative",
            locales=[DocumentLocale(lang="en", title="Mont Blanc from the air", description="...")],
        )

        self.session_add(self.image)
        self.session.flush()

        self._add_association(Association.create(self.area1, self.image), user_id)
        self.session.flush()

    def test_post_success(self):
        body = {
            "area_type": "range",
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type":"Polygon","coordinates":[[[668518.249382151,5728802.39591739],[668518.249382151,5745465.66808356],[689156.247019149,5745465.66808356],[689156.247019149,5728802.39591739],[668518.249382151,5728802.39591739]]]}',  # noqa
            },
            "locales": [{"lang": "en", "title": "Chartreuse"}],
            "associations": {"images": [{"document_id": self.image.document_id}]},
        }
        body, doc = self.post_success(body, user="moderator")
        self._assert_geometry(body)

        version = doc.versions[0]

        archive_map = version.document_archive
        assert archive_map.area_type == "range"

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Chartreuse"

        archive_geometry = version.document_geometry_archive
        assert archive_geometry.version == doc.geometry.version
        assert archive_geometry.geom_detail is not None

    def test_put_success_all_as_moderator(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.area1.document_id,
                "version": self.area1.version,
                "area_type": "admin_limits",
                "quality": quality_types[1],
                "geometry": {
                    "version": self.area1.geometry.version,
                    "geom_detail": '{"type":"Polygon","coordinates":[[[668519.249382151,5728802.39591739],[668518.249382151,5745465.66808356],[689156.247019149,5745465.66808356],[689156.247019149,5728802.39591739],[668519.249382151,5728802.39591739]]]}',  # noqa
                },
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
                "associations": {"images": []},
            },
        }
        (body, area) = self.put_success_all(body, self.area1, user="moderator", cache_version=3)

        # version with lang 'en'
        version_en = area.versions[-1]

        # geometry has been changed because the user is a moderator
        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 2

    def test_put_success_figures_only(self):
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.area1.document_id,
                "version": self.area1.version,
                "area_type": "admin_limits",
                "quality": quality_types[1],
                "locales": [{"lang": "en", "title": "Chartreuse", "version": self.locale_en.version}],
            },
        }
        (body, area) = self.put_success_figures_only(body, self.area1)

        assert area.area_type == "admin_limits"

    def test_put_success_lang_only(self):
        body = {
            "message": "Changing lang",
            "document": {
                "document_id": self.area1.document_id,
                "version": self.area1.version,
                "area_type": "range",
                "quality": quality_types[1],
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }
        (body, area) = self.put_success_lang_only(body, self.area1)

        assert area.get_locale("en").title == "New title"

    def test_put_update_geometry_fail(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.area1.document_id,
                "version": self.area1.version,
                "area_type": "admin_limits",
                "geometry": {
                    "version": self.area1.geometry.version,
                    "geom_detail": '{"type":"Polygon","coordinates":[[[668519.249382151,5728802.39591739],[668518.249382151,5745465.66808356],[689156.247019149,5745465.66808356],[689156.247019149,5728802.39591739],[668519.249382151,5728802.39591739]]]}',  # noqa
                },
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }
        headers = self.add_authorization_header(username="contributor")
        response = self.app_put_json(
            self._prefix + "/" + str(self.area1.document_id), body, headers=headers, status=403
        )

        body = response.json
        assert body["status"] == "error"
        assert body["name"] == "Forbidden"
        assert body["description"] == "No permission to change the geometry"

    def _assert_geometry(self, body):
        assert body.get("geometry") is not None
        geometry = body.get("geometry")
        assert geometry.get("version") is not None
        assert geometry.get("geom_detail") is not None

        geom = geometry.get("geom_detail")
        polygon = shape(json.loads(geom))
        assert isinstance(polygon, Polygon)
