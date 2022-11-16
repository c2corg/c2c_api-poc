from copy import deepcopy
import pytest
from c2corg_api.legacy.models.association import Association
from c2corg_api.legacy.models.document import DocumentGeometry, UpdateType
from flask_camp.models import DocumentVersion
from c2corg_api.legacy.models.feed import update_feed_document_create
from c2corg_api.legacy.models.route import Route, RouteLocale
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.legacy.views.document import DocumentRest
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.models import ROUTE_TYPE, WAYPOINT_TYPE
from json import loads


class TestDocumentRevertRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/documents/revert"
        self._add_test_data()
        self.session.commit()

    def test_revert_latest_version_id(self):
        headers = self.add_authorization_header(username="moderator")

        document_id = self.waypoint2["id"]
        version_id = self.waypoint2_v2["version_id"]
        request_body = {"document_id": document_id, "lang": "en", "version_id": version_id}

        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)
        self.assertErrorsContain(response.json, "Bad Request")

    def test_revert_waypoint(self):
        headers = self.add_authorization_header(username="moderator")

        document_id = self.waypoint2["id"]
        lang = "en"
        version_id = self.waypoint2["version_id"]
        initial_count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        request_body = {"document_id": document_id, "lang": lang, "version_id": version_id}
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        response = self.get("/waypoints/" + str(document_id), status=200)
        body = response.json
        assert body["elevation"] == 4810
        geom = loads(body["geometry"]["geom"])
        assert geom["coordinates"][0] == 635957
        assert geom["coordinates"][1] == 5723605
        for locale in body["locales"]:
            if locale["lang"] == lang:
                assert locale["title"] == "Mont Blanc"

        # check a new version has been created
        count = self.session.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).count()
        assert count == initial_count + 1

    def test_revert_route(self):
        headers = self.add_authorization_header(username="moderator")

        route_id = self.route1["id"]
        route_version_id = self.route1["version_id"]
        route_lang = "fr"
        request_body = {"document_id": route_id, "lang": route_lang, "version_id": route_version_id}
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        response = self.get("/routes/" + str(route_id), status=200)
        body = response.json
        assert body["elevation_max"] == 1500
        assert body["activities"] == ["skitouring"]
        for locale in body["locales"]:
            if locale["lang"] == route_lang:
                assert locale["title"] == "Mont Blanc du ciel"
                assert locale["title_prefix"] == "Mount Everest"

        # Now revert the main waypoint as well and check the title prefix
        # of the route has been updated:
        waypoint_id = self.waypoint2["id"]
        waypoint_lang = "en"
        waypoint_version_id = self.waypoint2["version_id"]
        request_body = {"document_id": waypoint_id, "lang": waypoint_lang, "version_id": waypoint_version_id}
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        response = self.get("/routes/" + str(route_id), status=200)
        body = response.json
        for locale in body["locales"]:
            if locale["lang"] == route_lang:
                assert locale["title"] == "Mont Blanc du ciel"
                assert locale["title_prefix"] == "Mont Blanc"

    def create_document(self, data, **kwargs):
        return self.post(
            "/v7/documents",
            json={"comment": "creation", "document": {"data": data}} | kwargs.pop("json", {}),
            **kwargs,
        )

    def modify_document(self, document, data, **kwargs):
        document_id = self._get_document_id(document)
        new_version = deepcopy(document)
        new_version["data"] = data

        return self.post(
            f"/v7/document/{document_id}",
            json={"comment": "modify", "document": new_version} | kwargs.pop("json", {}),
            **kwargs,
        )

    def _add_waypoint(self, locales):
        return self.create_document(
            data={
                "type": WAYPOINT_TYPE,
                "waypoint_type": "summit",
                "elevation": 4810,
                "locales": locales,
                "geometry": {"geom": {"type": "Point", "coordinates": [635957, 5723605]}},
                "associations": {},
            }
        )

    def _add_route(self, locales, main_waypoint_id, geometry):
        return self.create_document(
            data={
                "type": ROUTE_TYPE,
                "quality": "draft",
                "activities": ["skitouring"],
                "elevation_max": 1500,
                "elevation_min": 700,
                "main_waypoint_id": main_waypoint_id,
                "locales": locales,
                "geometry": geometry,
                "associations": {"waypoint": []},
            }
        )

    def _add_test_data(self):

        self.optimized_login("contributor")
        self.waypoint1 = self._add_waypoint(locales={"fr": {"lang": "fr", "title": "Dent de Crolles"}}).json["document"]
        self.waypoint2 = self._add_waypoint(locales={"en": {"lang": "en", "title": "Mont Blanc"}}).json["document"]
        self.waypoint3 = self._add_waypoint(locales={"en": {"lang": "en", "title": "Mont de Grange"}}).json["document"]

        data = deepcopy(self.waypoint2["data"])
        data["elevation"] = 8848
        data["locales"]["en"] = {"lang": "en", "title": "Mount Everest"}
        data["geometry"]["geom"]["coordinates"] = [0, 0]
        self.waypoint2_v2 = self.modify_document(self.waypoint2, data).json["document"]

        self.initial_route1_geometry = {
            "geom": {"type": "Point", "coordinates": [635961, 5723624]},
            "geom_detail": {"type": "LineString", "coordinates": [[635956, 5723604], [635966, 5723644]]},
        }

        self.route1 = self._add_route(
            main_waypoint_id=self.waypoint2["id"],
            geometry=self.initial_route1_geometry,
            locales={"fr": {"lang": "fr", "title": "Mont Blanc du ciel"}},
        ).json["document"]

        data = deepcopy(self.route1["data"])
        data["activities"] = ["skitouring", "hiking"]
        data["elevation_max"] = 4500
        data["main_waypoint_id"] = self.waypoint3["id"]
        data["locales"]["fr"] = {"lang": "fr", "title": "Some new route name"}
        data["geometry"]["geom"]["coordinates"] = [0, 0]
        self.route1_v2 = self.modify_document(self.route1, data).json["document"]
