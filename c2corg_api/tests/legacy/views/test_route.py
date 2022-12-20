import pytest
import datetime
import json

from c2corg_api.legacy.models.area import Area
from c2corg_api.legacy.models.area_association import AreaAssociation
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.association import Association, AssociationLog
from c2corg_api.legacy.models.book import Book
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.outing import Outing, OutingLocale
from c2corg_api.legacy.models.topo_map import TopoMap
from c2corg_api.legacy.models.topo_map_association import TopoMapAssociation
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.tests.legacy.search import reset_search_index

# from c2corg_api.views.route import check_title_prefix
from c2corg_api.models.common.attributes import quality_types
from shapely.geometry import shape, LineString

from c2corg_api.legacy.models.route import Route, RouteLocale, ArchiveRoute, ArchiveRouteLocale, ROUTE_TYPE
from c2corg_api.legacy.models.document import DocumentGeometry, DocumentLocale
from c2corg_api.legacy.models.document_topic import DocumentTopic
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from shapely.geometry.point import Point


class TestRouteRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/routes", ROUTE_TYPE, Route, ArchiveRoute, ArchiveRouteLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_get_collection(self):
        body = self.get_collection()
        doc = body["documents"][0]
        assert "height_diff_access" not in doc

    def test_get_collection_paginated(self):
        self.get("/routes?offset=invalid", status=400)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 0}), [], 4)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 1}), [self.route4.document_id], 4)
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}), [self.route4.document_id, self.route3.document_id], 4
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 1, "limit": 2}), [self.route3.document_id, self.route2.document_id], 4
        )

    def test_get_collection_lang(self):
        self.get_collection_lang()

    def test_get_collection_for_waypoint(self):
        reset_search_index(self.session)

        response = self.get(self._prefix + "?w=" + str(self.waypoint.document_id), status=200)

        documents = response.json["documents"]

        assert response.json["total"] == 1
        assert documents[0]["document_id"] == self.route.document_id

    def test_get_collection_has_geom(self):
        body = self.get_collection()
        doc = body["documents"][3]
        assert doc["geometry"]["has_geom_detail"] == True

    def test_get_collection_search(self):
        reset_search_index(self.session)

        body = self.get_collection_search({"act": "skitouring"})
        assert body.get("total") == 3
        assert len(body.get("documents")) == 3

        body = self.get_collection_search({"act": "skitouring", "limit": 2})
        assert body.get("total") == 3
        assert len(body.get("documents")) == 2

        body = self.get_collection_search({"hdif": "700,900"})
        assert body.get("total") == 2

    def test_get(self):
        body = self.get_custom(self.route)
        assert body.get("activities") == self.route.activities
        self._assert_geometry(body)
        assert "climbing_outdoor_type" not in body
        assert "elevation_min" in body
        assert body["glacier_gear"] == "no"

        locale_en = self.get_locale("en", body.get("locales"))
        assert "Main waypoint title" == locale_en.get("title_prefix")
        assert 1 == locale_en.get("topic_id")

        assert "main_waypoint_id" in body
        assert "associations" in body
        associations = body.get("associations")
        assert "waypoints" in associations
        assert "routes" in associations
        assert "recent_outings" in associations
        assert "images" in associations
        assert "articles" in associations
        assert "books" in associations

        linked_waypoints = associations.get("waypoints")
        assert 1 == len(linked_waypoints)
        assert self.waypoint.document_id == linked_waypoints[0].get("document_id")
        # check waypoint data in listing
        self.assertEqual(
            self.waypoint.locales[0].access_period, linked_waypoints[0].get("locales")[0].get("access_period")
        )
        assert "geometry" in linked_waypoints[0]
        assert "geom" in linked_waypoints[0].get("geometry")

        linked_routes = associations.get("routes")
        assert 1 == len(linked_routes)
        assert self.route4.document_id == linked_routes[0].get("document_id")
        # check route data in listing
        assert self.route4.climbing_outdoor_type == linked_routes[0].get("climbing_outdoor_type")
        # TODO with geometry now
        # assert 'geometry' not in linked_routes[0]

        linked_articles = associations.get("articles")
        assert 1 == len(linked_articles)
        assert self.article1.document_id == linked_articles[0].get("document_id")

        linked_books = associations.get("books")
        assert 1 == len(linked_books)
        assert self.book1.document_id == linked_books[0].get("document_id")

        recent_outings = associations.get("recent_outings")
        assert 1 == recent_outings["total"]
        # TODO documents are now in `documents` and not `outings`
        assert 1 == len(recent_outings["documents"])
        assert self.outing1.document_id == recent_outings["documents"][0].get("document_id")
        # check outing data in listing
        assert self.outing1.public_transport == recent_outings["documents"][0].get("public_transport")
        assert "type" in recent_outings["documents"][0]

        assert "maps" in body
        topo_map = body.get("maps")[0]
        assert topo_map.get("code") == "3232ET"
        self.assertEqual(topo_map.get("locales")[0].get("title"), "Belley")

    def test_get_version(self):
        self.get_version(self.route, self.route_version)

    def test_get_version_without_activity(self):
        """Tests that old route versions without activity include the fields
        of all activities.
        """
        self.route_version.document_archive.activities = []
        self.session.flush()
        body = self.get_version(self.route, self.route_version)
        locale = body["document"]["locales"][0]
        assert "title" in locale

    def test_get_cooked(self):
        self.get_cooked(self.route)

    def test_get_cooked_with_defaulting(self):
        self.get_cooked_with_defaulting(self.route)

    def test_get_lang(self):
        body = self.get_lang(self.route)

        self.assertEqual("Mont Blanc from the air", body.get("locales")[0].get("title"))
        self.assertEqual("Main waypoint title", body.get("locales")[0].get("title_prefix"))

    def test_get_new_lang(self):
        self.get_new_lang(self.route)

    def test_get_404(self):
        self.get_404()

    def test_get_edit(self):
        response = self.get(self._prefix + "/" + str(self.route.document_id) + "?e=1", status=200)
        body = response.json

        assert "maps" in body
        assert "areas" not in body
        assert "associations" in body
        associations = body["associations"]
        assert "waypoints" in associations
        assert "routes" in associations
        assert "xreports" in associations
        assert "images" not in associations
        assert "users" not in associations

    @pytest.mark.skip(reason="caching is handled and tested in flask-camp")
    def test_get_caching(self):
        self.get_caching(self.route)

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info(self):
        body, locale = self.get_info(self.route, "en")
        assert locale.get("lang") == "en"
        assert locale.get("title_prefix") == self.locale_en.title_prefix

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_best_lang(self):
        body, locale = self.get_info(self.route, "es")
        assert locale.get("lang") == "fr"

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_404(self):
        self.get_info_404()

    @pytest.mark.skip(reason="useless test: empty payload...")
    def test_post_error(self):
        body = self.post_error({})
        errors = body.get("errors")
        assert len(errors) == 2
        self.assertError(errors, "activities", "Required")
        self.assertError(errors, "associations.waypoints", "at least one waypoint required")

    def test_post_empty_activities_and_associations_error(self):
        body = self.post_error({"activities": []})
        errors = body.get("errors")
        assert len(errors) == 2
        self.assertError(errors, "activities", "Shorter than minimum length 1")
        self.assertError(errors, "associations.waypoints", "at least one waypoint required")

    def test_post_invalid_activity(self):
        body_post = {
            "activities": ["cooking"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        assert errors[0].get("description") == "invalid value: cooking"
        assert errors[0].get("name") == "activities"

    def test_post_missing_title(self):
        body_post = {
            "activities": ["skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en"}],
        }
        self.post_missing_title(body_post)

    def test_post_non_whitelisted_attribute(self):
        body = {
            "activities": ["hiking"],
            "protected": True,
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        self.post_non_whitelisted_attribute(body)

    def test_post_missing_content_type(self):
        self.post_missing_content_type({})

    def test_post_success(self):
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        body, doc = self.post_success(body)
        self._assert_geometry(body)
        self._assert_default_geometry(body)

        version = doc.versions[0]

        archive_route = version.document_archive
        assert archive_route.activities == ["hiking", "skitouring"]
        assert archive_route.elevation_max == 1500
        assert archive_route.durations == ["1"]

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Some nice loop"

        archive_geometry = version.document_geometry_archive
        assert archive_geometry.version == doc.geometry.version
        assert archive_geometry.geom_detail is not None
        assert archive_geometry.geom is not None

        assert doc.main_waypoint_id == self.waypoint.document_id
        assert body.get("main_waypoint_id") == self.waypoint.document_id
        assert archive_route.main_waypoint_id == self.waypoint.document_id

        self.assertEqual(self.waypoint.locales[0].title, doc.locales[0].title_prefix)

        # check that a link for intersecting areas is created
        links = self.session.query(AreaAssociation).filter(AreaAssociation.document_id == doc.document_id).all()
        assert len(links) == 1
        self.assertEqual(links[0].area_id, self.area1.document_id)

        # check that a link to the main waypoint is created
        association_main_wp = self.session.query(Association).get((self.waypoint.document_id, doc.document_id))
        assert association_main_wp is not None

        association_main_wp_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == self.waypoint.document_id)
            .filter(AssociationLog.child_document_id == doc.document_id)
            .first()
        )
        assert association_main_wp_log is not None

    def test_post_success_3d(self):
        """Tests that routes with 3D tracks can be created and read."""
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "geometry": {
                "geom_detail": '{"type": "LineString", "coordinates": '
                + "[[635956, 5723604, 1200], [635966, 5723644, 1210]]}"
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }

        _, doc = self.post_success(body)
        response = self.get(self._prefix + "/" + str(doc.document_id), status=200)
        body = response.json

        geometry = body["geometry"]
        geom = json.loads(geometry["geom"])
        assert len(geom["coordinates"]) == 2
        self.assertCoodinateEquals(geom["coordinates"], [635961.0, 5723624.0])

        geom_detail = json.loads(geometry["geom_detail"])
        assert len(geom_detail["coordinates"]) == 2
        assert len(geom_detail["coordinates"][0]) == 3
        self.assertCoodinateEquals(geom_detail["coordinates"][0], [635956.0, 5723604.0, 1200.0])
        self.assertCoodinateEquals(geom_detail["coordinates"][1], [635966.0, 5723644.0, 1210.0])

    def test_post_wrong_geom_type(self):
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "Point", "coordinates": ' + "[635956, 5723604]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "description": "...", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        errors = self.post_wrong_geom_type(body)
        self.assertEqual(
            errors[0]["description"],
            "Invalid geometry type. Expected: " "['LINESTRING', 'MULTILINESTRING']. Got: POINT.",
        )

    def test_post_corrupted_geojson_geom(self):
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": '
                + "[[[[[[635956, 5723604, 12345, 67890, 13579]]]]]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "description": "...", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        errors = self.post_wrong_geom_type(body)
        self.assertEqual(
            errors[0]["description"],
            'Invalid geometry: {"type": '
            '"LineString", "coordinates": '
            "[[[[[[635956, 5723604, 12345, 67890, 13579]]]]]]}",
        )

        body = {
            "activities": ["hiking", "skitouring"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom": '{"type": "Point", "coordinates": [NaN, NaN]}',
                "geom_detail": None,
            },
            "locales": [{"lang": "en", "title": "Some nice loop"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        errors = self.post_wrong_geom_type(body)
        self.assertEqual(errors[0]["description"], 'Invalid geometry: {"type": ' '"Point", "coordinates": [NaN, NaN]}')

    def test_post_success_3d_multiline(self):
        """Tests that routes with 3D multiline tracks can be created and read."""
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "geometry": {
                "geom_detail": '{"type": "MultiLineString", "coordinates": '
                + "[[[635956, 5723604, 1200], [635966, 5723644, 1210]]]}"
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }

        _, doc = self.post_success(body)
        response = self.get(self._prefix + "/" + str(doc.document_id), status=200)
        body = response.json

        geometry = body["geometry"]
        geom = json.loads(geometry["geom"])
        assert len(geom["coordinates"]) == 2
        self.assertCoodinateEquals(geom["coordinates"], [635961.0, 5723624.0])

        geom_detail = json.loads(geometry["geom_detail"])
        assert len(geom_detail["coordinates"]) == 1
        assert len(geom_detail["coordinates"][0]) == 2
        assert len(geom_detail["coordinates"][0][0]) == 3
        self.assertCoodinateEquals(geom_detail["coordinates"][0][0], [635956.0, 5723604.0, 1200.0])
        self.assertCoodinateEquals(geom_detail["coordinates"][0][1], [635966.0, 5723644.0, 1210.0])

    def test_post_success_4d(self):
        """Tests that routes with 4D tracks can be created and read."""
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "geometry": {
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604, 1200, 12345], "
                "[635966, 5723644, 1210, 12346]]}"
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }

        _, doc = self.post_success(body)
        response = self.get(self._prefix + "/" + str(doc.document_id), status=200)
        body = response.json

        geometry = body["geometry"]
        geom = json.loads(geometry["geom"])
        assert len(geom["coordinates"]) == 2
        self.assertCoodinateEquals(geom["coordinates"], [635961.0, 5723624.0])

        geom_detail = json.loads(geometry["geom_detail"])
        assert len(geom_detail["coordinates"]) == 2
        assert len(geom_detail["coordinates"][0]) == 4
        self.assertCoodinateEquals(geom_detail["coordinates"][0], [635956.0, 5723604.0, 1200.0, 12345])
        self.assertCoodinateEquals(geom_detail["coordinates"][1], [635966.0, 5723644.0, 1210.0, 12346])

    def test_post_default_geom_multi_line(self):
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "MultiLineString", "coordinates": '
                + "[[[635956, 5723604], [635966, 5723644]], "
                "[[635966, 5723614], [635976, 5723654]]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        body, doc = self.post_success(body)
        assert doc.geometry.geom is not None
        assert doc.geometry.geom_detail is not None
        self._assert_default_geometry(body)

    def test_post_default_geom_from_main_wp(self):
        body = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        body, doc = self.post_success(body)
        assert doc.geometry.geom is not None
        assert doc.geometry.geom_detail is None
        self._assert_default_geometry(body, x=635956, y=5723604)

    def test_post_default_geom_from_associated_wps(self):
        body = {
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
        }
        body, doc = self.post_success(body, skip_validation=True)
        assert doc.geometry.geom is not None
        assert doc.geometry.geom_detail is None
        self._assert_default_geometry(body, x=635956, y=5723604)

    def test_post_main_wp_without_association(self):
        body_post = {
            "main_waypoint_id": self.waypoint.document_id,
            "activities": ["hiking", "skitouring"],
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "durations": ["1"],
            "locales": [{"lang": "en", "title": "Some nice loop", "gear": "shoes"}],
            # no association for the main waypoint
            "associations": {"waypoints": [{"document_id": self.waypoint2.document_id}]},
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        self.assertError(errors, "main_waypoint_id", "no association for the main waypoint")

    def test_put_wrong_document_id(self):
        body = {
            "document": {
                "document_id": "9999999",
                "version": self.route.version,
                "activities": ["hiking"],
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            }
        }
        self.put_wrong_document_id(body)

    def test_put_wrong_document_version(self):
        body = {
            "document": {
                "document_id": self.route.document_id,
                "version": -9999,
                "activities": ["skitouring"],
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            }
        }
        self.put_wrong_version(body, self.route.document_id)

    @pytest.mark.skip(reason="Locales are not versionned in the new model")
    def test_put_wrong_locale_version(self):
        body = {
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "activities": ["skitouring"],
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": -9999,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            }
        }
        self.put_wrong_version(body, self.route.document_id)

    def test_put_wrong_ids(self):
        body = {
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "activities": ["skitouring"],
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            }
        }
        self.put_wrong_ids(body, self.route.document_id)

    def test_put_no_document(self):
        self.put_put_no_document(self.route.document_id)

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.route.geometry.version,
                    "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635976, 5723654]]}",
                },
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            },
        }
        (body, route) = self.put_success_all(body, self.route)
        self._assert_default_geometry(body, x=635961, y=5723624)

        assert route.elevation_max == 1600
        locale_en = route.get_locale("en")
        assert locale_en.description == "..."
        assert locale_en.gear == "none"

        # version with lang 'en'
        versions = route.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "Mont Blanc from the air"
        assert archive_locale.gear == "none"

        archive_document_en = version_en.document_archive
        assert archive_document_en.activities == ["skitouring"]
        assert archive_document_en.elevation_max == 1600

        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 2

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Mont Blanc du ciel"
        assert archive_locale.gear == "paraglider"

    def test_put_success_figures_only(self):
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "glacier_gear": "no",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "paraglider",
                        "version": self.locale_en.version,
                        "title_prefix": "Should be ignored",
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            },
        }
        (body, route) = self.put_success_figures_only(body, self.route)

        assert route.elevation_max == 1600

    def test_put_success_new_track_with_default_geom(self):
        """Test that a provided default geometry (`geom`) is used instead of
        obtaining the geom from a track (`geom_detail`).
        """
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "glacier_gear": "no",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "paraglider",
                        "version": self.locale_en.version,
                        "title_prefix": "Should be ignored",
                    }
                ],
                "geometry": {
                    "version": self.route.geometry.version,
                    "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635976, 5723654]]}",
                    "geom": '{"type": "Point", "coordinates": [635000, 5723000]}',
                },
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            },
        }
        (body, route) = self.put_success_figures_only(body, self.route)
        self._assert_default_geometry(body, x=635000, y=5723000)

    def test_put_success_main_wp_changed(self):
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.route.document_id,
                "main_waypoint_id": self.waypoint2.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "glacier_gear": "no",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "paraglider",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint2.document_id}]},
            },
        }
        (body, route) = self.put_success_figures_only(body, self.route, user="moderator")
        # tests that the default geometry has not changed (main wp has changed
        # but the route has a track)
        self._assert_default_geometry(body)

        assert route.main_waypoint_id == self.waypoint2.document_id
        locale_en = route.get_locale("en")
        assert locale_en.title_prefix == self.waypoint2.get_locale("en").title

        # check that a link to the new main waypoint is created
        association_main_wp = self.session.query(Association).get((self.waypoint2.document_id, route.document_id))
        assert association_main_wp is not None

        association_main_wp_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == self.waypoint2.document_id)
            .filter(AssociationLog.child_document_id == route.document_id)
            .first()
        )
        assert association_main_wp_log is not None

    def test_put_success_lang_only(self):
        body = {
            "message": "Changing lang",
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "glacier_gear": "no",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "gear": "none",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            },
        }
        (body, route) = self.put_success_lang_only(body, self.route)

        assert route.get_locale("en").gear == "none"

    def test_put_success_new_lang(self):
        """Test updating a document by adding a new locale."""
        body = {
            "message": "Adding lang",
            "document": {
                "document_id": self.route.document_id,
                "version": self.route.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "glacier_gear": "no",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "durations": ["1"],
                "locales": [{"lang": "es", "title": "Mont Blanc del cielo", "description": "...", "gear": "si"}],
                "associations": {"waypoints": [{"document_id": self.waypoint.document_id}]},
            },
        }
        (body, route) = self.put_success_new_lang(body, self.route)

        assert route.get_locale("es").gear == "si"

    def test_history(self):
        id = self.route.document_id
        langs = ["fr", "en"]
        for lang in langs:
            body = self.get("/document/%d/history/%s" % (id, lang))
            username = "contributor"
            user_id = self.global_userids[username]

            title = body.json["title"]
            versions = body.json["versions"]
            assert len(versions) == 1
            assert getattr(self == "locale_" + lang).title, title
            for r in versions:
                assert r["name"] == "contributor"
                assert "username" not in r
                assert r["user_id"] == user_id
                assert "written_at" in r
                assert "version_id" in r

    def test_history_no_lang(self):
        id = self.route.document_id
        self.get("/document/%d/history/es" % id, status=404)

    def test_history_no_doc(self):
        self.get("/document/99999/history/es", status=404)

    def _assert_geometry(self, body):
        assert body.get("geometry") is not None
        geometry = body.get("geometry")
        assert geometry.get("version") is not None
        assert geometry.get("geom_detail") is not None

        geom = geometry.get("geom_detail")
        line = shape(json.loads(geom))
        assert isinstance(line, LineString)
        self.assertAlmostEqual(line.coords[0][0], 635956)
        self.assertAlmostEqual(line.coords[0][1], 5723604)
        self.assertAlmostEqual(line.coords[1][0], 635966)
        self.assertAlmostEqual(line.coords[1][1], 5723644)

    def _assert_default_geometry(self, body, x=635961, y=5723624):
        assert body.get("geometry") is not None
        geometry = body.get("geometry")
        assert geometry.get("version") is not None
        assert geometry.get("geom") is not None

        geom = geometry.get("geom")
        point = shape(json.loads(geom))
        assert isinstance(point, Point)
        self.assertAlmostEqual(point.x, x)
        self.assertAlmostEqual(point.y, y)

    def test_update_prefix_title(self):
        self.route.locales.append(
            RouteLocale(lang="es", title="Mont Blanc del cielo", description="...", gear="paraglider")
        )
        self.route.main_waypoint_id = self.waypoint.document_id
        self.session.flush()
        self.session_refresh(self.route)
        check_title_prefix(self.route, create=False)
        self.session.expire_all()

        route = self.session.query(Route).get(self.route.document_id)
        locale_en = route.get_locale("en")
        assert locale_en.version == 1
        assert locale_en.title_prefix == self.waypoint.get_locale("en").title
        locale_fr = route.get_locale("fr")
        assert locale_fr.version == 1
        assert locale_fr.title_prefix == self.waypoint.get_locale("fr").title
        locale_es = route.get_locale("es")
        assert locale_es.version == 1
        assert locale_es.title_prefix == self.waypoint.get_locale("fr").title

    @pytest.mark.skip(reason="This view is not relevant in new model")
    def test_get_associations_history(self):
        self._get_association_logs(self.route)

    def _add_test_data(self):
        self.route = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
        )

        self.locale_en = RouteLocale(
            lang="en",
            title="Mont Blanc from the air",
            description="...",
            gear="paraglider",
            title_prefix="Main waypoint title",
            document_topic=DocumentTopic(topic_id=1),
        )

        self.locale_fr = RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", gear="paraglider")

        self.route.locales.append(self.locale_en)
        self.route.locales.append(self.locale_fr)

        self.route.geometry = DocumentGeometry(
            geom_detail="SRID=3857;LINESTRING(635956 5723604, 635966 5723644)", geom="SRID=3857;POINT(635961 5723624)"
        )

        self.session_add(self.route)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.route, user_id)
        self.route_version = self.session_query_first(DocumentVersion, document_id=self.route.document_id)

        self.article1 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article1)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route, child_document=self.article1), user_id)

        self.book1 = Book(activities=["hiking"], book_types=["biography"])
        self.session_add(self.book1)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.book1, child_document=self.route), user_id)

        self.route2 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
            locales=[
                RouteLocale(lang="en", title="Mont Blanc from the air", description="...", gear="paraglider"),
                RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", gear="paraglider"),
            ],
        )
        self.session_add(self.route2)
        self.session.flush()
        DocumentRest.create_new_version(self.route2, user_id)

        self.route3 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=500,
            height_diff_down=500,
            durations="1",
            locales=[
                RouteLocale(lang="en", title="Mont Blanc from the air", description="...", gear="paraglider"),
                RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", gear="paraglider"),
            ],
        )

        self.route3.geometry = DocumentGeometry(geom="SRID=3857;POINT(0 0)")
        self.session_add(self.route3)
        self.session.flush()
        DocumentRest.create_new_version(self.route3, user_id)

        self.route4 = Route(
            activities=["rock_climbing"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=500,
            height_diff_down=500,
            durations="1",
            climbing_outdoor_type="single",
        )
        self.route4.locales.append(
            RouteLocale(lang="en", title="Mont Blanc from the air", description="...", gear="paraglider")
        )
        self.route4.locales.append(
            RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", gear="paraglider")
        )
        self.session_add(self.route4)

        # add some associations
        self.waypoint = Waypoint(
            waypoint_type="climbing_outdoor",
            elevation=4,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
        )
        self.waypoint.locales.append(
            WaypointLocale(
                lang="en", title="Mont Granier 1 (en)", description="...", access="yep", access_period="yapa"
            )
        )
        self.waypoint.locales.append(
            WaypointLocale(
                lang="fr", title="Mont Granier 1 (fr)", description="...", access="ouai", access_period="yapa"
            )
        )
        self.session_add(self.waypoint)
        self.waypoint2 = Waypoint(
            waypoint_type="summit", elevation=4, geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        )
        self.waypoint2.locales.append(
            WaypointLocale(lang="en", title="Mont Granier 2 (en)", description="...", access="yep")
        )
        self.session_add(self.waypoint2)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route, child_document=self.route4), user_id)
        self._add_association(Association.create(parent_document=self.route4, child_document=self.route), user_id)
        self._add_association(Association.create(parent_document=self.waypoint, child_document=self.route), user_id)

        # add a map
        topo_map = TopoMap(
            code="3232ET",
            editor="IGN",
            scale="25000",
            locales=[DocumentLocale(lang="fr", title="Belley")],
            geometry=DocumentGeometry(
                geom_detail="SRID=3857;POLYGON((635900 5723600, 635900 5723700, 636000 5723700, 636000 5723600, 635900 5723600))"
            ),  # noqa
        )
        self.session_add(topo_map)
        self.session.flush()
        self.session_add(TopoMapAssociation(document=self.route, topo_map=topo_map))

        self.outing1 = Outing(
            activities=["skitouring"],
            date_start=datetime.date(2016, 1, 1),
            date_end=datetime.date(2016, 1, 1),
            public_transport=True,
            locales=[OutingLocale(lang="en", title="...", description="...", weather="sunny")],
        )
        self.session_add(self.outing1)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route, child_document=self.outing1), user_id)

        self.outing2 = Outing(
            # redirects_to=self.outing1.document_id,
            activities=["skitouring"],
            date_start=datetime.date(2016, 1, 1),
            date_end=datetime.date(2016, 1, 1),
            locales=[OutingLocale(lang="en", title="...", description="...", weather="sunny")],
        )
        self.session_add(self.outing2)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route, child_document=self.outing2), user_id)
        self.session.flush()

        # add areas
        self.area1 = Area(
            area_type="range",
            geometry=DocumentGeometry(
                geom_detail="SRID=3857;POLYGON((635900 5723600, 635900 5723700, 636000 5723700, 636000 5723600, 635900 5723600))"  # noqa
            ),
        )
        self.area2 = Area(area_type="range", locales=[DocumentLocale(lang="fr", title="France")])

        self.session_add_all([self.area1, self.area2])
        self.session.flush()
