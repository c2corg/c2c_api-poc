import pytest
import json

from c2corg_api.legacy.models.route import Route
from c2corg_api.legacy.models.topo_map import ArchiveTopoMap, TopoMap, MAP_TYPE
from c2corg_api.legacy.models.topo_map_association import TopoMapAssociation
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.tests.legacy.search import reset_search_index
from c2corg_api.models.common.attributes import quality_types
from shapely.geometry import shape, Polygon

from c2corg_api.legacy.models.document import DocumentGeometry, ArchiveDocumentLocale, DocumentLocale
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest


class TestTopoMapRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/maps", MAP_TYPE, TopoMap, ArchiveTopoMap, ArchiveDocumentLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_post_success(self):
        body = {
            "editor": "IGN",
            "scale": "25000",
            "code": "3432OT",
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type":"Polygon","coordinates":[[[668518.249382151,5728802.39591739],[668518.249382151,5745465.66808356],[689156.247019149,5745465.66808356],[689156.247019149,5728802.39591739],[668518.249382151,5728802.39591739]]]}',  # noqa
            },
            "locales": [{"lang": "en", "title": "Lac d'Annecy"}],
        }
        body, doc = self.post_success(body, user="moderator")
        assert body["geometry"].get("geom_detail") is not None

        version = doc.versions[0]

        archive_map = version.document_archive
        assert archive_map.editor == "IGN"
        assert archive_map.scale == "25000"
        assert archive_map.code == "3432OT"

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Lac d'Annecy"

        archive_geometry = version.document_geometry_archive
        assert archive_geometry.version == doc.geometry.version
        assert archive_geometry.geom_detail is not None
        assert archive_geometry.geom_detail is not None

        # TODO check that a link for intersecting documents is created ?

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.map1.document_id,
                "version": self.map1.version,
                "quality": quality_types[1],
                "editor": "IGN",
                "scale": "25000",
                "code": "3433OT",
                "geometry": {
                    "version": self.map1.geometry.version,
                    "geom_detail": '{"type":"Polygon","coordinates":[[[668519.249382151,5728802.39591739],[668518.249382151,5745465.66808356],[689156.247019149,5745465.66808356],[689156.247019149,5728802.39591739],[668519.249382151,5728802.39591739]]]}',  # noqa
                },
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }
        (body, map1) = self.put_success_all(body, self.map1, user="moderator")

        assert map1.code == "3433OT"
        locale_en = map1.get_locale("en")
        assert locale_en.title == "New title"

        # version with lang 'en'
        versions = map1.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "New title"

        archive_document_en = version_en.document_archive
        assert archive_document_en.scale == "25000"
        assert archive_document_en.code == "3433OT"

        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 2

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Lac d'Annecy"

        # TODO check that the links to intersecting documents are updated

    def _add_test_data(self):
        self.map1 = TopoMap(editor="IGN", scale="25000", code="3431OT")

        self.locale_en = DocumentLocale(lang="en", title="Lac d'Annecy")
        self.locale_fr = DocumentLocale(lang="fr", title="Lac d'Annecy")

        self.map1.locales.append(self.locale_en)
        self.map1.locales.append(self.locale_fr)

        self.map1.geometry = DocumentGeometry(
            geom_detail="SRID=3857;POLYGON((611774 5706934,611774 5744215,"
            "642834 5744215,642834 5706934,611774 5706934))"
        )

        self.session_add(self.map1)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.map1, user_id)

        self.map2 = TopoMap(editor="IGN", scale="25000", code="3432OT")
        self.session_add(self.map2)
        self.map3 = TopoMap(editor="IGN", scale="25000", code="3433OT")
        self.session_add(self.map3)
        self.map4 = TopoMap(editor="IGN", scale="25000", code="3434OT")
        self.map4.locales.append(DocumentLocale(lang="en", title="Lac d'Annecy"))
        self.map4.locales.append(DocumentLocale(lang="fr", title="Lac d'Annecy"))
        self.session_add(self.map4)
        self.session.flush()

        self.waypoint1 = Waypoint(
            waypoint_type="summit", geometry=DocumentGeometry(geom="SRID=3857;POINT(677461.381691516 5740879.44638645)")
        )
        self.waypoint2 = Waypoint(
            waypoint_type="summit", geometry=DocumentGeometry(geom="SRID=3857;POINT(693666.031687976 5741108.7574713)")
        )
        route_geom = "SRID=3857;LINESTRING(668518 5728802, 668528 5728812)"
        self.route = Route(activities=["skitouring"], geometry=DocumentGeometry(geom_detail=route_geom))

        self.session_add_all([self.waypoint1, self.waypoint2, self.route])
        self.session_add(TopoMapAssociation(document=self.waypoint2, topo_map=self.map1))
        self.session.flush()
