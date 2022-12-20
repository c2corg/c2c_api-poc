import pytest
import datetime
import json
from unittest.mock import patch

# from c2corg_api.legacy.caching import cache_document_listing, cache_document_history, cache_document_version
# from c2corg_api import caching
from c2corg_api.legacy.models.area import Area
from c2corg_api.legacy.models.area_association import AreaAssociation
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.association import Association
from c2corg_api.legacy.models.cache_version import get_cache_key, CacheVersion
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.feed import update_feed_document_create
from c2corg_api.legacy.models.outing import Outing, OutingLocale
from c2corg_api.legacy.models.topo_map import TopoMap
from c2corg_api.legacy.models.topo_map_association import TopoMapAssociation
from c2corg_api.legacy.search import elasticsearch_config

# from c2corg_api.search.mappings.route_mapping import SearchRoute
from c2corg_api.tests.legacy.search import reset_search_index

# from c2corg_api.views.document_listings import get_documents
# from c2corg_api.views.waypoint import waypoint_documents_config
from c2corg_api.models.common.attributes import quality_types

# from dogpile.cache.api import NO_VALUE
from shapely.geometry import shape, Point

from c2corg_api.legacy.models.route import Route, RouteLocale
from c2corg_api.legacy.models.waypoint import (
    Waypoint,
    WaypointLocale,
    ArchiveWaypoint,
    ArchiveWaypointLocale,
    WAYPOINT_TYPE,
)
from c2corg_api.legacy.models.document import DocumentGeometry, ArchiveDocumentGeometry, DocumentLocale, DOCUMENT_TYPE
from c2corg_api.legacy.models.document_topic import DocumentTopic
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest


class TestWaypointRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/waypoints", WAYPOINT_TYPE, Waypoint, ArchiveWaypoint, ArchiveWaypointLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_get_collection(self):
        body = self.get_collection()
        doc = body["documents"][0]
        assert "waypoint_type" in doc
        assert "elevation" in doc
        assert "geometry" in doc
        assert "routes_quantity" not in doc
        locale = doc["locales"][0]
        assert "title" in locale
        assert "summary" in locale
        assert "description" not in locale
        assert "areas" in doc

    def test_get_collection_lang(self):
        self.get_collection_lang()

    def test_get_collection_paginated(self):
        self.get("/waypoints?offset=invalid", status=400)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 0}), [], 4)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 1}), [self.waypoint4.document_id], 4)
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}), [self.waypoint4.document_id, self.waypoint3.document_id], 4
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 1, "limit": 2}), [self.waypoint3.document_id, self.waypoint2.document_id], 4
        )

    def test_get_collection_caching(self):
        cache_key_2 = get_cache_key(self.waypoint2.document_id, None, WAYPOINT_TYPE)
        cache_key_3 = get_cache_key(self.waypoint3.document_id, None, WAYPOINT_TYPE)
        cache_key_4 = get_cache_key(self.waypoint4.document_id, None, WAYPOINT_TYPE)

        assert cache_document_listing.get(cache_key_2) == NO_VALUE
        assert cache_document_listing.get(cache_key_3) == NO_VALUE
        assert cache_document_listing.get(cache_key_4) == NO_VALUE

        # check that documents returned in the response are cached
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}), [self.waypoint4.document_id, self.waypoint3.document_id], 4
        )

        assert cache_document_listing.get(cache_key_3) != NO_VALUE
        assert cache_document_listing.get(cache_key_4) != NO_VALUE

        # check that values are returned from the cache
        fake_cache_value = {"document_id": "fake_id"}
        cache_document_listing.set(cache_key_3, fake_cache_value)

        body = self.get_collection({"offset": 1, "limit": 2})
        self.assertResultsEqual(body, ["fake_id", self.waypoint2.document_id], 4)
        assert cache_document_listing.get(cache_key_2) != NO_VALUE

    def test_get_collection_search(self):
        reset_search_index(self.session)

        self.assertResultsEqual(
            self.get_collection_search({"wtyp": "climbing_outdoor,summit"}),
            [
                self.waypoint4.document_id,
                self.waypoint3.document_id,
                self.waypoint2.document_id,
                self.waypoint.document_id,
            ],
            4,
        )

        body = self.get_collection_search({"wtyp": "climbing_outdoor,summit", "limit": 2})
        assert body.get("total") == 4
        assert len(body.get("documents")) == 2

        body = self.get_collection_search({"a": str(self.area2.document_id)})
        assert body.get("total") == 1

        body = self.get_collection_search({"walt": "2000"})
        assert body.get("total") == 1

    def test_get_collection_search_bbox(self):
        reset_search_index(self.session)

        self.assertResultsEqual(
            self.get_collection_search({"bbox": "659000,5694000,660000,5695000"}), [self.waypoint4.document_id], 1
        )

    def test_get_collection_big_offset(self):
        url = "{}?offset=10000".format(self._prefix)
        response = self.get(url, status=400)
        self.assertErrorsContain(response.json, "Bad Request")

        url = "{}?offset=9970&limit=30".format(self._prefix)
        self.get(url, status=200)

    def test_get(self):
        body = self.get_custom(self.waypoint)
        self._assert_geometry(body)
        assert "waypoint_type" in body
        assert "routes_quantity" not in body

        assert "associations" in body
        associations = body.get("associations")
        assert "articles" in associations
        assert "books" in associations
        assert "images" in associations
        assert "waypoints" in associations

        linked_articles = associations.get("articles")
        assert len(linked_articles) == 1
        assert self.article1.document_id == linked_articles[0].get("document_id")

        linked_waypoints = associations.get("waypoint_children")
        assert 1 == len(linked_waypoints)
        assert self.waypoint4.document_id == linked_waypoints[0].get("document_id")
        assert "type" in linked_waypoints[0]
        assert "geometry" in linked_waypoints[0]
        assert "geom" in linked_waypoints[0].get("geometry")

        all_linked_routes = associations.get("all_routes")
        linked_routes = all_linked_routes["documents"]
        assert 2 == len(linked_routes)
        linked_route = linked_routes[1]
        assert "type" in linked_route
        assert linked_route["document_id"] == self.route1.document_id
        self.assertEqual(linked_route.get("locales")[0].get("title_prefix"), "Mont Blanc :")
        assert linked_routes[0]["document_id"] == self.route3.document_id
        assert "geometry" in linked_routes[1]
        # TODO not returning `geom_detail` anymore
        assert "geom" in linked_routes[1].get("geometry")

        assert "maps" in body
        assert 1 == len(body.get("maps"))
        topo_map = body.get("maps")[0]
        assert "type" in topo_map
        assert topo_map.get("code") == "3232ET"
        self.assertEqual(topo_map.get("locales")[0].get("title"), "Belley")

        assert "areas" in body
        area = body.get("areas")[0]
        assert "type" in area
        assert area.get("area_type") == "range"
        self.assertEqual(area.get("locales")[0].get("title"), "France")

        # TODO `outings` renamed to `documents`
        recent_outings = associations.get("recent_outings")
        assert 2 == recent_outings["total"]
        assert 2 == len(recent_outings["documents"])
        self.assertEqual(
            {self.outing1.document_id, self.outing3.document_id},
            {recent_outings["documents"][0].get("document_id"), recent_outings["documents"][1].get("document_id")},
        )
        assert "type" in recent_outings["documents"][0]

        locale_en = self.get_locale("en", body.get("locales"))
        assert 1 == locale_en.get("topic_id")

    def test_get_with_empty_arrays(self):
        """Test-case for https://github.com/c2corg/v6_api/issues/231"""
        self.assertEqual(self.waypoint2.rock_types, [])
        response = self.get(self._prefix + "/" + str(self.waypoint2.document_id), status=200)
        body = response.json
        assert "rock_types" in body
        self.assertEqual(body["rock_types"], [])

    def test_get_edit(self):
        response = self.get(self._prefix + "/" + str(self.waypoint.document_id) + "?e=1", status=200)
        body = response.json

        assert "recent_outings" not in body["associations"]
        assert "maps" in body
        assert "areas" not in body
        assert "associations" in body
        associations = body["associations"]
        assert "waypoints" in associations
        assert "waypoint_children" in associations
        assert "routes" not in associations
        assert "images" not in associations

    def test_get_version(self):
        self.get_version(self.waypoint, self.waypoint_version)

    def test_get_version_etag(self):
        url = "{0}/{1}/en/{2}".format(self._prefix, str(self.waypoint.document_id), str(self.waypoint_version.id))
        response = self.get(url, status=200)

        # check that the ETag header is set
        headers = response.headers
        etag = headers.get("ETag")
        assert etag is not None

        # then request the document again with the etag
        headers = {"If-None-Match": etag}
        self.get(url, status=304, headers=headers)

    def test_get_version_caching(self):
        url = "{0}/{1}/en/{2}".format(self._prefix, str(self.waypoint.document_id), str(self.waypoint_version.id))
        cache_key = "{0}-{1}".format(
            get_cache_key(self.waypoint.document_id, "en", WAYPOINT_TYPE), self.waypoint_version.id
        )

        cache_value = cache_document_version.get(cache_key)
        assert cache_value == NO_VALUE

        # check that the response is cached
        self.get(url, status=200)

        cache_value = cache_document_version.get(cache_key)
        assert cache_value != NO_VALUE

        # check that values are returned from the cache
        fake_cache_value = {"document": "fake doc"}
        cache_document_version.set(cache_key, fake_cache_value)

        response = self.get(url, status=200)
        body = response.json
        assert body == fake_cache_value

    def test_get_cooked(self):
        self.get_cooked(self.waypoint)

    def test_get_cooked_with_defaulting(self):
        self.get_cooked_with_defaulting(self.waypoint)

    def test_get_lang(self):
        body = self.get_lang(self.waypoint)

        self.assertEqual("Mont Granier", body.get("locales")[0].get("title"))

    def test_get_new_lang(self):
        self.get_new_lang(self.waypoint)

    def test_get_404(self):
        self.get_404()

    def test_get_redirected_wp(self):
        response = self.get(self._prefix + "/" + str(self.waypoint5.document_id), status=200)
        body = response.json

        assert "redirects_to" in body
        assert body["redirects_to"] == self.waypoint.document_id
        assert set(body["available_langs"]) == set(["en", "fr"])

    def test_get_etag(self):
        response = self.get(self._prefix + "/" + str(self.waypoint.document_id), status=200)

        # check that the ETag header is set
        headers = response.headers
        etag = headers.get("ETag")
        assert etag is not None

        # then request the document again with the etag
        headers = {"If-None-Match": etag}
        response = self.get(self._prefix + "/" + str(self.waypoint.document_id), status=304, headers=headers)

    def test_get_caching(self):
        self.get_caching(self.waypoint)

    def test_get_cache_down(self):
        """Check that the request does not fail even if Redis errors."""
        detail_cache_mock = patch(
            "c2corg_api.views.document.cache_document_detail.get_or_create", side_effect=Exception("Redis down")
        )
        listings_cache_mock = patch(
            "c2corg_api.views.document_listings.cache_document_listing." "get_or_create_multi",
            side_effect=Exception("Redis down"),
        )

        with detail_cache_mock, listings_cache_mock:
            self.get(self._prefix + "/" + str(self.waypoint.document_id), status=200)
            assert caching.cache_status.up is False

    def test_get_cache_down_known(self):
        """Check that no request to the cache is made if a request to the
        cache failed in the last 30 seconds.
        """
        detail_cache_mock = patch(
            "c2corg_api.views.document.cache_document_detail.get_or_create", side_effect=Exception("Redis down")
        )
        listings_cache_mock = patch(
            "c2corg_api.views.document_listings.cache_document_listing." "get_or_create_multi",
            side_effect=Exception("Redis down"),
        )

        with detail_cache_mock as fn1, listings_cache_mock as fn2:
            caching.cache_status.request_failure()
            self.get(self._prefix + "/" + str(self.waypoint.document_id), status=200)
            assert fn1.called is False
            assert fn2.called is False

    def test_get_info(self):
        body, locale = self.get_info(self.waypoint, "en")
        assert locale.get("lang") == "en"

    def test_get_info_best_lang(self):
        body, locale = self.get_info(self.waypoint, "es")
        assert locale.get("lang") == "fr"

    def test_get_info_404(self):
        self.get_info_404()

    def test_get_info_redirect(self):
        response = self.get(self._prefix + "/" + str(self.waypoint5.document_id) + "/en/info", status=200)
        body = response.json

        assert "redirects_to" in body
        assert body["redirects_to"] == self.waypoint.document_id
        assert set(body["available_langs"]) == set(["en", "fr"])

    def test_post_error(self):
        body = self.post_error({})
        errors = body.get("errors")
        self.assertCorniceRequired(errors[0], "waypoint_type")

    def test_post_missing_title(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3200,
            "geometry": {"geom": '{"type": "Point", "coordinates": [1, 1]}'},
            "locales": [{"lang": "en"}],
        }
        self.post_missing_title(body)

    def test_post_missing_geometry(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3200,
            "locales": [{"lang": "en", "title": "Mont Pourri", "access": "y"}],
        }
        self.post_missing_geometry(body)

    def test_post_missing_geom(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3200,
            "geometry": {},
            "locales": [{"lang": "en", "title": "Mont Pourri", "access": "y"}],
        }
        self.post_missing_geom(body)

    def test_post_missing_locales(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3200,
            "geometry": {"geom": '{"type": "Point", "coordinates": [1, 1]}'},
            "locales": [],
        }
        self.post_missing_locales(body)

    def test_post_same_locale_twice(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3200,
            "geometry": {"geom": '{"type": "Point", "coordinates": [1, 1]}'},
            "locales": [
                {"lang": "en", "title": "Mont Pourri", "access": "y"},
                {"lang": "en", "title": "Mont Pourri", "access": "y"},
            ],
        }
        self.post_same_locale_twice(body)

    def test_post_missing_elevation(self):
        body = {
            "waypoint_type": "summit",
            "geometry": {"geom": '{"type": "Point", "coordinates": [1, 1]}'},
            "locales": [{"lang": "en", "title": "Mont Pourri", "access": "y"}],
        }
        self.post_missing_field(body, "elevation")

    def test_post_non_whitelisted_attribute(self):
        body = {
            "waypoint_type": "summit",
            "elevation": 3779,
            "geometry": {"geom": '{"type": "Point", "coordinates": [1, 1]}'},
            "protected": True,
            "locales": [{"lang": "en", "title": "Mont Pourri", "access": "y"}],
        }
        self.post_non_whitelisted_attribute(body)

    def test_post_missing_content_type(self):
        self.post_missing_content_type({})

    def test_post_invalid_waypoint_type(self):
        body_post = {
            "geometry": {
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "swimming-pool",
            "elevation": 3779,
            "locales": [{"lang": "en", "title": "Mont Pourri"}],
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        self.assertTrue(errors[0].get("description").startswith('"swimming-pool" is not one of'))
        assert errors[0].get("name") == "waypoint_type"

    def test_post_empty_assoc_in_new_w_document(self):
        body = {
            "document_id": 0,
            "version": 2345,
            "geometry": {
                "document_id": 5678,
                "version": 6789,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "summit",
            "elevation": 3779,
            "locales": [{"id": 3456, "version": 4567, "lang": "en", "title": "Mont Pourri", "access": "y"}],
            "associations": {
                "waypoints": [],
                "waypoint_children": [],
                "routes": [],
                "all_routes": {"total": 0, "documents": []},
                "users": [],
                "recent_outings": {"total": 0, "documents": []},
                "articles": [],
                "images": [],
                "areas": [],
            },
        }

        body, doc = self.post_success(body, user="moderator")

    def test_post_invalid_association_with_personal_article(self):
        body_post = {
            "document_id": 1234,
            "version": 2345,
            "geometry": {
                "document_id": 5678,
                "version": 6789,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "summit",
            "elevation": 3779,
            "locales": [{"id": 3456, "version": 4567, "lang": "en", "title": "Mont Pourri", "access": "y"}],
            "associations": {"articles": [{"document_id": self.article2.document_id}]},
        }
        body = self.post_error(body_post, user="contributor2")
        self.assertError(
            body["errors"],
            "Bad Request",
            "no rights to modify associations with article {}".format(self.article2.document_id),
        )

    def test_post_invalid_association_with_redirected_doc(self):
        body_post = {
            "document_id": 1234,
            "version": 2345,
            "geometry": {
                "document_id": 5678,
                "version": 6789,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "summit",
            "elevation": 3779,
            "locales": [{"id": 3456, "version": 4567, "lang": "en", "title": "Mont Pourri", "access": "y"}],
            "associations": {"waypoints": [{"document_id": self.waypoint5.document_id}]},
        }
        body = self.post_error(body_post, user="contributor2")
        self.assertError(
            body["errors"],
            "associations.waypoints",
            'document "{}" does not exist or is redirected'.format(self.waypoint5.document_id),
        )

    def test_post_success(self):
        body = {
            "document_id": 1234,
            "version": 2345,
            "geometry": {
                "document_id": 5678,
                "version": 6789,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "summit",
            "elevation": 3779,
            "locales": [{"id": 3456, "version": 4567, "lang": "en", "title": "Mont Pourri", "access": "y"}],
            "associations": {"waypoint_children": [{"document_id": self.waypoint2.document_id}]},
        }
        waypoint2_cache_key = self.session.query(CacheVersion).get(self.waypoint2.document_id).version

        body, doc = self.post_success(body)
        self._assert_geometry(body, "geom")

        # test that document_id and version was reset
        assert body.get("document_id") != 1234
        assert body.get("version") == 1
        self.assertNotEqual(doc.locales[0].id, 3456)
        self.assertEqual(body.get("locales")[0].get("version"), 1)
        assert doc.geometry.document_id == doc.document_id
        assert doc.geometry.version == 1
        version = doc.versions[0]

        archive_waypoint = version.document_archive
        assert archive_waypoint.waypoint_type == "summit"
        assert archive_waypoint.elevation == 3779

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Mont Pourri"
        assert archive_locale.access == "y"

        archive_geometry = version.document_geometry_archive
        assert archive_geometry.version == doc.geometry.version
        assert archive_geometry.document_id == doc.geometry.document_id
        assert archive_geometry.geom is not None
        assert archive_geometry.geom_detail is not None

        # check that a link for intersecting areas is created
        links = self.session.query(AreaAssociation).filter(AreaAssociation.document_id == doc.document_id).all()
        assert len(links) == 1
        self.assertEqual(links[0].area_id, self.area1.document_id)

        # check that a link for intersecting maps is created
        links = self.session.query(TopoMapAssociation).filter(TopoMapAssociation.document_id == doc.document_id).all()
        assert len(links) == 1
        self.assertEqual(links[0].topo_map_id, self.topo_map1.document_id)

        # check that a link to the child waypoint is created
        association_wp = self.session.query(Association).get((doc.document_id, self.waypoint2.document_id))
        assert association_wp is not None

        # check that the cache key for wp 2 is incremented, which was included
        # as association
        self.check_cache_version(self.waypoint2.document_id, waypoint2_cache_key + 1)

        # check that a change is created in the feed
        feed_change = self.get_feed_change(doc.document_id)
        assert feed_change is not None
        self.assertEqual(feed_change.user_ids, [self.global_userids["contributor"]])
        self.assertEqual(feed_change.area_ids, [self.area1.document_id])

    def test_post_wrong_geom_type(self):
        body = {
            "document_id": 1234,
            "version": 2345,
            "geometry": {
                "document_id": 5678,
                "version": 6789,
                "geom": '{"type": "LineString", "coordinates": ' "[[635956, 5723604], [635960, 5723610]]}",
                "geom_detail": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "waypoint_type": "summit",
            "elevation": 3779,
            "locales": [{"id": 3456, "version": 4567, "lang": "en", "title": "Mont Pourri", "access": "y"}],
            "associations": {"waypoint_children": [{"document_id": self.waypoint2.document_id}]},
        }
        errors = self.post_wrong_geom_type(body)
        self.assertEqual(errors[0]["description"], "Invalid geometry type. Expected: " "['POINT']. Got: LINESTRING.")

    def test_put_wrong_document_id(self):
        body = {
            "document": {
                "document_id": "9999999",
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [{"lang": "en", "title": "Mont Granier", "description": "...", "access": "n"}],
            }
        }
        self.put_wrong_document_id(body)

    def test_put_wrong_document_version(self):
        body = {
            "document": {
                "document_id": self.waypoint.document_id,
                "version": -9999,
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [{"lang": "en", "title": "Mont Granier", "description": "...", "access": "n"}],
            }
        }
        self.put_wrong_version(body, self.waypoint.document_id)

    def test_put_wrong_locale_version(self):
        body = {
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [
                    {"lang": "en", "title": "Mont Granier", "description": "...", "access": "n", "version": -9999}
                ],
            }
        }
        self.put_wrong_version(body, self.waypoint.document_id)

    def test_put_wrong_ids(self):
        body = {
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier",
                        "description": "A.",
                        "access": "n",
                        "version": self.locale_en.version,
                    }
                ],
            }
        }
        self.put_wrong_ids(body, self.waypoint.document_id)

    def test_put_no_document(self):
        self.put_put_no_document(self.waypoint.document_id)

    def test_put_missing_elevation(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
            },
        }
        self.put_missing_field(body, self.waypoint, "elevation")

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "orientations": None,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier!",
                        "description": "A.",
                        "access": "n",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.waypoint.geometry.version,
                    "geom": '{"type": "Point", "coordinates": [635957, 5723605]}',  # noqa
                },
                "associations": {
                    "waypoint_children": [{"document_id": self.waypoint2.document_id}],
                    "routes": [{"document_id": self.route1.document_id}],
                    "articles": [{"document_id": self.article1.document_id}],
                },
            },
        }
        (body, waypoint) = self.put_success_all(body, self.waypoint, cache_version=4, user="moderator")

        assert waypoint.elevation == 1234
        locale_en = waypoint.get_locale("en")
        assert locale_en.description == "A."
        assert locale_en.access == "n"

        # version with lang 'en'
        versions = waypoint.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "Mont Granier!"
        assert archive_locale.access == "n"

        archive_document_en = version_en.document_archive
        assert archive_document_en.waypoint_type == "summit"
        assert archive_document_en.elevation == 1234

        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 2

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Mont Granier"
        assert archive_locale.access == "ouai"

        # check that the title_prefix of an associated route (that the wp
        # it the main wp of) was updated
        route = self.session.query(Route).get(self.route1.document_id)
        route_locale_en = route.get_locale("en")
        assert route_locale_en.title_prefix == "Mont Granier!"

        # check that the route was updated in the search index
        search_doc = SearchRoute.get(id=route.document_id, index=elasticsearch_config["index"])
        assert search_doc["title_en"] == "Mont Granier! : Mont Blanc from the air"

        # check that the links for intersecting areas are updated
        links = (
            self.session.query(AreaAssociation).filter(AreaAssociation.document_id == self.waypoint.document_id).all()
        )
        assert len(links) == 1
        self.assertEqual(links[0].area_id, self.area1.document_id)

        # check that the links for intersecting maps are updated
        links = (
            self.session.query(TopoMapAssociation)
            .filter(TopoMapAssociation.document_id == self.waypoint.document_id)
            .all()
        )
        assert len(links) == 1
        self.assertEqual(links[0].topo_map_id, self.topo_map1.document_id)

        # check that a link to the child waypoint is created
        association_wp = self.session.query(Association).get((waypoint.document_id, self.waypoint2.document_id))
        assert association_wp is not None

        # check that a link to the child article is created
        association_a = self.session.query(Association).get((waypoint.document_id, self.article1.document_id))
        assert association_a is not None

        # check that the feed change is updated
        feed_change = self.get_feed_change(waypoint.document_id)
        assert feed_change is not None
        self.assertEqual(feed_change.user_ids, [self.global_userids["contributor"]])
        self.assertEqual(feed_change.area_ids, [self.area1.document_id])

    def test_put_success_figures_and_lang_only(self):
        body_put = {
            "message": "Update",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier",
                        "description": "A.",
                        "access": "n",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": None,
            },
        }
        (body, waypoint) = self.put_success_all(body_put, self.waypoint, cache_version=3)
        document_id = body.get("document_id")
        assert body.get("version") == 2

        self.session.expire_all()
        # check that a new archive_document was created
        archive_count = (
            self.session.query(self._model_archive)
            .filter(getattr(self._model_archive, "document_id") == document_id)
            .count()
        )
        assert archive_count == 2

        # check that a new archive_document_locale was created
        archive_locale_count = (
            self.session.query(self._model_archive_locale)
            .filter(document_id == getattr(self._model_archive_locale, "document_id"))
            .count()
        )
        assert archive_locale_count == 3

        # check that a new archive_document_geometry was created
        archive_geometry_count = (
            self.session.query(ArchiveDocumentGeometry)
            .filter(document_id == ArchiveDocumentGeometry.document_id)
            .count()
        )
        assert archive_geometry_count == 1

        assert waypoint.elevation == 1234
        locale_en = waypoint.get_locale("en")
        assert locale_en.description == "A."
        assert locale_en.access == "n"

        # version with lang 'en'
        versions = waypoint.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "Mont Granier"
        assert archive_locale.access == "n"

        archive_document_en = version_en.document_archive
        assert archive_document_en.waypoint_type == "summit"
        assert archive_document_en.elevation == 1234

        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 1

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Mont Granier"
        assert archive_locale.access == "ouai"

        # check that the links to intersecting areas are not updated,
        # because the geometry did not change
        links = (
            self.session.query(AreaAssociation).filter(AreaAssociation.document_id == self.waypoint.document_id).all()
        )
        assert len(links) == 1
        self.assertEqual(links[0].area_id, self.area2.document_id)

    def test_put_success_figures_only(self):
        """Test updating a document with only changes to the figures."""
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 1234,
                "locales": [],
            },
        }
        (body, waypoint) = self.put_success_figures_only(body, self.waypoint)

        assert waypoint.elevation == 1234

    def test_put_boolean_default_values(self):
        """Test-case for https://github.com/c2corg/v6_api/issues/229"""
        assert self.waypoint.blanket_unstaffed is None
        assert self.waypoint.matress_unstaffed is None
        assert self.waypoint.gas_unstaffed is None
        assert self.waypoint.heating_unstaffed is None

        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 1234,
                "blanket_unstaffed": True,
                "matress_unstaffed": False,
                "gas_unstaffed": None,
                "locales": [],
            },
        }
        (_, waypoint) = self.put_success_figures_only(body, self.waypoint)

        assert waypoint.blanket_unstaffed == True
        assert waypoint.matress_unstaffed == False
        assert waypoint.gas_unstaffed is None
        assert waypoint.heating_unstaffed is None

    def test_put_success_lang_only(self):
        """Test updating a document with only changes to a locale."""
        body = {
            "message": "Changing lang",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 2203,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier",
                        "description": "...",
                        "access": "no",
                        "version": self.locale_en.version,
                    }
                ],
            },
        }
        (body, waypoint) = self.put_success_lang_only(body, self.waypoint)

        assert waypoint.get_locale("en").access == "no"

    def test_put_success_new_lang(self):
        """Test updating a document by adding a new locale."""
        body = {
            "message": "Adding lang",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 2203,
                "locales": [
                    {
                        "id": 1234,
                        "version": 2345,
                        "lang": "es",
                        "title": "Mont Granier",
                        "description": "...",
                        "access": "si",
                    }
                ],
            },
        }
        (body, waypoint) = self.put_success_new_lang(body, self.waypoint)

        assert waypoint.get_locale("es").access == "si"
        assert waypoint.get_locale("es").version != 2345
        assert waypoint.get_locale("es").id != 1234

    def test_put_add_geometry(self):
        """Tests adding a geometry to a waypoint without geometry."""
        # first create a waypoint with no geometry
        waypoint = Waypoint(waypoint_type="summit", elevation=3779)

        locale_en = WaypointLocale(lang="en", title="Mont Pourri", access="y")
        waypoint.locales.append(locale_en)

        self.session_add(waypoint)
        self.session.flush()
        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(waypoint, user_id)

        # then add a geometry to the waypoint
        body_put = {
            "message": "Adding geom",
            "document": {
                "document_id": waypoint.document_id,
                "version": waypoint.version,
                "quality": quality_types[1],
                "geometry": {"geom": '{"type": "Point", "coordinates": [635956, 5723604]}'},
                "waypoint_type": "summit",
                "elevation": 3779,
                "locales": [],
            },
        }
        response = self.app_put_json(self._prefix + "/" + str(waypoint.document_id), body_put, status=403)

        headers = self.add_authorization_header(username="contributor")
        self.app_put_json(self._prefix + "/" + str(waypoint.document_id), body_put, headers=headers, status=200)

        response = self.get(self._prefix + "/" + str(waypoint.document_id), status=200)
        assert response.content_type == "application/json"

        body = response.json
        document_id = body.get("document_id")
        assert body.get("version") == body_put.get("document").get("version")

        # check that no new archive_document was created
        self.session.expire_all()
        document = self.session.query(self._model).get(document_id)

        # check that a new archive_document was created
        archive_count = (
            self.session.query(self._model_archive)
            .filter(getattr(self._model_archive, "document_id") == document_id)
            .count()
        )
        assert archive_count == 1

        # check that no new archive_document_locale was created
        archive_locale_count = (
            self.session.query(self._model_archive_locale)
            .filter(document_id == getattr(self._model_archive_locale, "document_id"))
            .count()
        )
        assert archive_locale_count == 1

        # check that a new archive_document_geometry was created
        archive_locale_count = (
            self.session.query(ArchiveDocumentGeometry)
            .filter(document_id == ArchiveDocumentGeometry.document_id)
            .count()
        )
        assert archive_locale_count == 1

        # check that new versions were created
        versions = document.versions
        assert len(versions) == 2

        # version with lang 'en'
        version_en = self.get_latest_version("en", versions)

        assert version_en.lang == "en"

        meta_data_en = version_en.history_metadata
        assert meta_data_en.comment == "Adding geom"
        assert meta_data_en.written_at is not None

    def test_put_merged_wp(self):
        """Tests updating a waypoint with `redirected_to` set."""
        body_put = {
            "message": "Updating",
            "document": {
                "document_id": self.waypoint5.document_id,
                "version": self.waypoint5.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 3779,
                "locales": [],
            },
        }

        headers = self.add_authorization_header(username="contributor")
        response = self.app_put_json(
            self._prefix + "/" + str(self.waypoint5.document_id), body_put, headers=headers, status=400
        )

        errors = response.json.get("errors")
        assert errors[0].get("description") == "can not update merged document"
        assert errors[0].get("name") == "Bad Request"

    def test_put_protected_no_permission(self):
        """Tests updating a protected waypoint as non-moderator."""
        body_put = {
            "message": "Updating",
            "document": {
                "document_id": self.waypoint4.document_id,
                "version": self.waypoint4.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 3779,
                "locales": [],
            },
        }

        headers = self.add_authorization_header(username="contributor")
        response = self.app_put_json(
            self._prefix + "/" + str(self.waypoint4.document_id), body_put, headers=headers, status=403
        )

        errors = response.json.get("errors")
        assert errors[0].get("description") == "No permission to change a protected document"
        assert errors[0].get("name") == "Forbidden"

    def test_put_protected_as_moderator(self):
        """Tests updating a protected waypoint as moderator."""
        body_put = {
            "message": "Updating",
            "document": {
                "document_id": self.waypoint4.document_id,
                "version": self.waypoint4.version,
                "quality": quality_types[1],
                "waypoint_type": "summit",
                "elevation": 3779,
                "locales": [],
            },
        }

        headers = self.add_authorization_header(username="moderator")
        self.app_put_json(self._prefix + "/" + str(self.waypoint4.document_id), body_put, headers=headers, status=200)

    def test_put_no_permission_for_association_change(self):
        """Test that non-moderator users can not remove associations."""
        body = {
            "message": "Update",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "orientations": None,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier!",
                        "description": "A.",
                        "access": "n",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.waypoint.geometry.version,
                    "geom": '{"type": "Point", "coordinates": [635957, 5723605]}',  # noqa
                },
                "associations": {
                    "waypoint_children": [
                        # association to waypoint 4 is removed
                    ],
                    "routes": [{"document_id": self.route1.document_id}],
                    "articles": [{"document_id": self.article1.document_id}],
                },
            },
        }
        headers = self.add_authorization_header(username="contributor")
        response = self.app_put_json(
            self._prefix + "/" + str(self.waypoint.document_id), body, headers=headers, status=400
        )
        body = response.json

        self.assertError(
            body["errors"],
            "Bad Request",
            "no rights to modify associations between document "
            "w ({}) and w ({})".format(self.waypoint.document_id, self.waypoint4.document_id),
        )

    def test_put_add_new_association(self):
        """Test that non-moderator users can add new associations."""
        body = {
            "message": "Update",
            "document": {
                "document_id": self.waypoint.document_id,
                "version": self.waypoint.version,
                "waypoint_type": "summit",
                "elevation": 1234,
                "orientations": None,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Granier!",
                        "description": "A.",
                        "access": "n",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.waypoint.geometry.version,
                    "geom": '{"type": "Point", "coordinates": [635957, 5723605]}',  # noqa
                },
                "associations": {
                    "waypoint_children": [
                        {"document_id": self.waypoint4.document_id},
                        {"document_id": self.waypoint2.document_id},
                    ],
                    "routes": [{"document_id": self.route1.document_id}],
                    "articles": [{"document_id": self.article1.document_id}],
                },
            },
        }
        headers = self.add_authorization_header(username="contributor")
        self.app_put_json(self._prefix + "/" + str(self.waypoint.document_id), body, headers=headers, status=200)

        association = self.session.query(Association).get((self.waypoint.document_id, self.waypoint2.document_id))
        assert association is not None

    def _assert_geometry(self, body, field="geom"):
        assert body.get("geometry") is not None
        geometry = body.get("geometry")
        assert geometry.get("version") is not None
        assert geometry.get(field) is not None

        geom = geometry.get(field)
        point = shape(json.loads(geom))
        assert isinstance(point, Point)
        self.assertAlmostEqual(point.x, 635956)
        self.assertAlmostEqual(point.y, 5723604)

    def test_history(self):
        id = self.waypoint.document_id
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

    def test_history_etag(self):
        id = self.waypoint.document_id

        response = self.get("/document/%d/history/%s" % (id, "fr"))

        # check that the ETag header is set
        headers = response.headers
        etag = headers.get("ETag")
        assert etag is not None

        # then request the document again with the etag
        headers = {"If-None-Match": etag}
        self.get("/document/%d/history/%s" % (id, "fr"), status=304, headers=headers)

    def test_history_caching(self):
        waypoint_id = self.waypoint.document_id
        cache_key = get_cache_key(waypoint_id, "fr", DOCUMENT_TYPE)

        cache_value = cache_document_history.get(cache_key)
        assert cache_value == NO_VALUE

        # check that the response is cached
        self.get("/document/%d/history/%s" % (waypoint_id, "fr"), status=200)

        cache_value = cache_document_history.get(cache_key)
        assert cache_value != NO_VALUE

        # check that values are returned from the cache
        fake_cache_value = {"title": "fake title"}
        cache_document_history.set(cache_key, fake_cache_value)

        response = self.get("/document/%d/history/%s" % (waypoint_id, "fr"), status=200)
        body = response.json
        assert body == fake_cache_value

    def test_get_documents_no_version(self):
        """Test that documents that do not have a version are skipped."""

        def search_documents(_, __):
            documents_ids = [self.waypoint.document_id, 999, self.waypoint2.document_id]
            return documents_ids, 3

        body = get_documents(waypoint_documents_config, meta_params={"lang": None}, search_documents=search_documents)

        documents = body.get("documents")
        assert len(documents) == 2

        assert documents[0]["document_id"] == self.waypoint.document_id
        assert documents[1]["document_id"] == self.waypoint2.document_id

    def test_get_documents_redirect(self):
        """Test that redirected documents are handled correctly."""

        def search_documents(_, __):
            documents_ids = [
                self.waypoint.document_id,
                self.waypoint5.document_id,  # with a redirect
                self.waypoint2.document_id,
            ]
            return documents_ids, 3

        body = get_documents(waypoint_documents_config, meta_params={"lang": None}, search_documents=search_documents)

        documents = body.get("documents")
        assert len(documents) == 2

        assert documents[0]["document_id"] == self.waypoint.document_id
        assert documents[1]["document_id"] == self.waypoint2.document_id

    def test_get_associations_history(self):
        self._get_association_logs(self.waypoint)

    def _add_test_data(self):
        self.waypoint = Waypoint(waypoint_type="summit", elevation=2203)

        self.locale_en = WaypointLocale(
            lang="en", title="Mont Granier", description="...", access="yep", document_topic=DocumentTopic(topic_id=1)
        )

        self.locale_fr = WaypointLocale(lang="fr", title="Mont Granier", description="...", access="ouai")

        self.waypoint.locales.append(self.locale_en)
        self.waypoint.locales.append(self.locale_fr)

        self.waypoint.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        self.session_add(self.waypoint)
        self.session.flush()
        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.waypoint, user_id)
        self.waypoint_version = self.session_query_first(DocumentVersion, document_id=self.waypoint.document_id)

        update_feed_document_create(self.waypoint, user_id)

        self.waypoint2 = Waypoint(
            waypoint_type="climbing_outdoor",
            elevation=2,
            rock_types=[],
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
        )
        self.session_add(self.waypoint2)

        self.waypoint3 = Waypoint(
            waypoint_type="summit", elevation=3, geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        )
        self.session_add(self.waypoint3)

        self.waypoint4 = Waypoint(
            waypoint_type="summit",
            elevation=4,
            protected=True,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(659775 5694854)"),
        )
        self.waypoint4.locales.append(WaypointLocale(lang="en", title="Mont Granier", description="...", access="yep"))
        self.waypoint4.locales.append(WaypointLocale(lang="fr", title="Mont Granier", description="...", access="ouai"))
        self.session_add(self.waypoint4)

        self.waypoint5 = Waypoint(
            waypoint_type="summit",
            elevation=3,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
        )
        self.waypoint5.locales.append(WaypointLocale(lang="en", title="Mont Granier", description="...", access="yep"))
        self.session_add(self.waypoint5)
        self.session.flush()

        DocumentRest.create_new_version(self.waypoint4, user_id)
        DocumentRest.create_new_version(self.waypoint5, user_id)

        # add some associations
        route1_geometry = DocumentGeometry(
            geom_detail="SRID=3857;LINESTRING(635956 5723604, 635966 5723644)", geom="SRID=3857;POINT(635961 5723624)"
        )
        self.route1 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
            main_waypoint_id=self.waypoint.document_id,
            geometry=route1_geometry,
        )
        self.route1.locales.append(
            RouteLocale(
                lang="en",
                title="Mont Blanc from the air",
                description="...",
                title_prefix="Mont Blanc :",
                gear="paraglider",
            )
        )
        self.session_add(self.route1)
        self.session.flush()
        self.route2 = Route(
            # redirects_to=self.route1.document_id,
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
            main_waypoint_id=self.waypoint.document_id,
        )
        self.route3 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
        )
        self.route3.locales.append(
            RouteLocale(
                lang="en",
                title="Mont Blanc from the air",
                description="...",
                title_prefix="Mont Blanc :",
                gear="paraglider",
            )
        )
        self.session_add(self.route2)
        self.session_add(self.route3)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.waypoint, child_document=self.waypoint4), user_id)
        self._add_association(Association.create(parent_document=self.waypoint, child_document=self.route1), user_id)
        self._add_association(Association.create(parent_document=self.waypoint, child_document=self.route2), user_id)
        self._add_association(Association.create(parent_document=self.waypoint4, child_document=self.route3), user_id)

        # article
        self.article1 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article1)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.waypoint, child_document=self.article1), user_id)

        self.article2 = Article(
            categories=["site_info"],
            activities=["hiking"],
            article_type="personal",
            locales=[DocumentLocale(lang="en", title="Lac d'Annecy")],
        )
        self.session_add(self.article2)
        self.session.flush()
        DocumentRest.create_new_version(self.article2, user_id)

        self.outing1 = Outing(
            activities=["skitouring"],
            date_start=datetime.date(2016, 1, 1),
            date_end=datetime.date(2016, 1, 3),
            locales=[OutingLocale(lang="en", title="...", description="...", weather="sunny")],
        )
        self.session_add(self.outing1)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route1, child_document=self.outing1), user_id)

        self.outing2 = Outing(
            # redirects_to=self.outing1.document_id,
            activities=["skitouring"],
            date_start=datetime.date(2016, 1, 1),
            date_end=datetime.date(2016, 1, 1),
            locales=[OutingLocale(lang="en", title="...", description="...", weather="sunny")],
        )

        self.outing3 = Outing(
            activities=["skitouring"],
            date_start=datetime.date(2015, 12, 31),
            date_end=datetime.date(2016, 1, 1),
            locales=[OutingLocale(lang="en", title="...", description="...", weather="sunny")],
        )
        self.session_add(self.outing2)
        self.session_add(self.outing3)
        self.session.flush()
        self._add_association(Association.create(parent_document=self.route1, child_document=self.outing2), user_id)
        self._add_association(Association.create(parent_document=self.route3, child_document=self.outing3), user_id)

        # add a map
        self.topo_map1 = TopoMap(
            code="3232ET",
            editor="IGN",
            scale="25000",
            locales=[DocumentLocale(lang="fr", title="Belley")],
            geometry=DocumentGeometry(
                geom_detail="SRID=3857;POLYGON((611774.917032556 5706934.10657514,611774.917032556 5744215.5846397,642834.402570357 5744215.5846397,642834.402570357 5706934.10657514,611774.917032556 5706934.10657514))"
            ),  # noqa
        )
        self.topo_map2 = TopoMap(
            code="3232ET", editor="IGN", scale="25000", locales=[DocumentLocale(lang="fr", title="Belley")]
        )
        self.session_add_all([self.topo_map1, self.topo_map2])
        self.session.flush()
        self.session_add(
            TopoMap(
                # redirects_to=self.topo_map1.document_id,
                code="3232ET",
                editor="IGN",
                scale="25000",
                locales=[DocumentLocale(lang="fr", title="Belley")],
                geometry=DocumentGeometry(
                    geom_detail="SRID=3857;POLYGON((611774.917032556 5706934.10657514,611774.917032556 5744215.5846397,642834.402570357 5744215.5846397,642834.402570357 5706934.10657514,611774.917032556 5706934.10657514))"
                ),  # noqa
            )
        )
        self.session_add(TopoMapAssociation(document=self.waypoint, topo_map=self.topo_map2))
        self.session.flush()

        # add areas
        self.area1 = Area(
            area_type="range",
            geometry=DocumentGeometry(
                geom_detail="SRID=3857;POLYGON((611774.917032556 5706934.10657514,611774.917032556 5744215.5846397,642834.402570357 5744215.5846397,642834.402570357 5706934.10657514,611774.917032556 5706934.10657514))"  # noqa
            ),
        )
        self.area2 = Area(area_type="range", locales=[DocumentLocale(lang="fr", title="France")])

        self.session_add_all([self.area1, self.area2])
        self.session_add(AreaAssociation(document=self.waypoint, area=self.area2))
        self.session.flush()
