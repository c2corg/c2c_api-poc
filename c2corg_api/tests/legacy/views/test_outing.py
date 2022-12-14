import pytest
from datetime import date, timedelta
import json

from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.association import Association, AssociationLog
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.feed import update_feed_document_create
from c2corg_api.legacy.models.image import Image
from c2corg_api.legacy.models.outing import Outing, ArchiveOuting, ArchiveOutingLocale, OutingLocale, OUTING_TYPE
from c2corg_api.legacy.models.user_profile import USERPROFILE_TYPE
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.tests.legacy.search import reset_search_index
from c2corg_api.models.common.attributes import quality_types
from shapely.geometry import shape, LineString

from c2corg_api.legacy.models.route import Route, RouteLocale
from c2corg_api.legacy.models.document import DocumentGeometry, DocumentLocale
from c2corg_api.legacy.models.document_topic import DocumentTopic
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from shapely.geometry.point import Point


class TestOutingRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/outings", OUTING_TYPE, Outing, ArchiveOuting, ArchiveOutingLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_get_collection(self):
        body = self.get_collection()
        assert len(body["documents"]) == 4
        doc1 = body["documents"][0]
        assert "frequentation" not in doc1
        assert "condition_rating" in doc1

        doc4 = body["documents"][3]
        assert "author" in doc4
        author = doc4["author"]
        assert "username" not in author
        assert author["name"] == "contributor"
        assert author["user_id"] == self.global_userids["contributor"]

        for doc in body["documents"]:
            # number of associated images
            assert "img_count" in doc
            self.assertEqual(doc["img_count"], 1 if doc["document_id"] == self.outing.document_id else 0)

    def test_get_collection_for_route(self):
        reset_search_index(self.session)
        response = self.get(self._prefix + "?r=" + str(self.route.document_id), status=200)
        documents = response.json["documents"]
        assert documents[0]["document_id"] == self.outing.document_id
        assert response.json["total"] == 1

    def test_get_collection_has_geom(self):
        reset_search_index(self.session)
        response = self.get(self._prefix + "?r=" + str(self.route.document_id), status=200)
        documents = response.json["documents"]
        assert documents[0]["geometry"]["has_geom_detail"] == True

    def test_get_collection_for_waypoint(self):
        reset_search_index(self.session)
        response = self.get(self._prefix + "?w=" + str(self.waypoint.document_id), status=200)

        documents = response.json["documents"]

        assert documents[0]["document_id"] == self.outing.document_id
        assert response.json["total"] == 1

    def test_get_collection_for_user(self):
        reset_search_index(self.session)
        response = self.get(self._prefix + "?u=" + str(self.global_userids["contributor"]), status=200)

        documents = response.json["documents"]

        assert documents[0]["document_id"] == self.outing.document_id
        assert response.json["total"] == 1

    def test_get_collection_paginated(self):
        self.get("/outings?offset=invalid", status=400)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 0}), [], 4)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 1}), [self.outing4.document_id], 4)
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}), [self.outing4.document_id, self.outing3.document_id], 4
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 1, "limit": 2}), [self.outing3.document_id, self.outing2.document_id], 4
        )

    def test_get_collection_lang(self):
        self.get_collection_lang()

    def test_get_collection_search(self):
        reset_search_index(self.session)

        self.assertResultsEqual(
            self.get_collection_search({"act": "skitouring"}),
            [self.outing4.document_id, self.outing3.document_id, self.outing2.document_id, self.outing.document_id],
            4,
        )

        body = self.get_collection_search({"act": "skitouring", "limit": 2})
        assert body.get("total") == 4
        assert len(body.get("documents")) == 2

        body = self.get_collection_search({"date": "2015-12-31,2016-01-02"})
        assert body.get("total") == 1

    def test_get(self):
        body = self.get_custom(self.outing)
        assert body.get("activities") == self.outing.activities
        self._assert_geometry(body)
        assert "frequentation" in body
        assert "maps" not in body

        assert "associations" in body
        associations = body.get("associations")
        assert "waypoints" not in associations
        assert "routes" in associations
        assert "xreports" in associations
        assert "images" in associations
        assert "users" in associations
        assert "articles" in associations

        linked_articles = associations.get("articles")
        assert len(linked_articles) == 1
        assert self.article1.document_id == linked_articles[0].get("document_id")

        linked_routes = associations.get("routes")
        assert len(linked_routes) == 1
        assert self.route.document_id == linked_routes[0].get("document_id")

        linked_users = associations.get("users")
        assert len(linked_users) == 1
        # TODO id -> document_id
        assert linked_users[0]["document_id"] == self.global_userids["contributor"]

        linked_images = associations.get("images")
        assert len(linked_images) == 1
        assert linked_images[0]["document_id"] == self.image.document_id
        assert "geometry" in linked_images[0]
        assert "geom" in linked_images[0].get("geometry")

        locale_en = self.get_locale("en", body.get("locales"))
        assert 1 == locale_en.get("topic_id")

    def test_get_edit(self):
        response = self.get(self._prefix + "/" + str(self.outing.document_id) + "?e=1", status=200)
        body = response.json

        assert "maps" not in body
        assert "areas" not in body
        assert "associations" in body
        associations = body["associations"]
        assert "waypoints" not in associations
        assert "routes" in associations
        assert "users" in associations
        assert "images" not in associations

    def test_get_version(self):
        self.get_version(self.outing, self.outing_version)

    def test_get_sort_asc(self):
        """Test ascending sorting of results for height_diff_up keyword."""
        reset_search_index(self.session)
        response = self.get(self._prefix + "?sort=height_diff_up", status=200)
        response_ids = [d["document_id"] for d in response.json["documents"]]
        outing_ids = [d.document_id for d in [self.outing3, self.outing4, self.outing2, self.outing]]
        assert response_ids == outing_ids

    def test_get_sort_desc(self):
        """Test descending sorting of results for elevation max keyword."""
        reset_search_index(self.session)
        response = self.get(self._prefix + "?sort=-elevation_max", status=200)
        response_ids = [d["document_id"] for d in response.json["documents"]]
        outing_ids = [d.document_id for d in [self.outing2, self.outing, self.outing4, self.outing3]]
        assert response_ids == outing_ids

    def test_get_sort_multi(self):
        """Test multi-criteria sorting (elevation_max: desc,
        height_diff_up: asc)"""
        reset_search_index(self.session)
        response = self.get(self._prefix + "?sort=-elevation_max,height_diff_up", status=200)
        response_ids = [d["document_id"] for d in response.json["documents"]]
        outing_ids = [d.document_id for d in [self.outing2, self.outing, self.outing4, self.outing3]]
        assert response_ids == outing_ids

    def test_get_sort_numeric_enum(self):
        """Test sorting with two different criteria:
        numeric (elevation_access) and enum (condition_rating)"""
        reset_search_index(self.session)
        response = self.get(self._prefix + "?sort=-elevation_access,condition_rating", status=200)
        response_ids = [d["document_id"] for d in response.json["documents"]]
        outing_ids = [d.document_id for d in [self.outing, self.outing4, self.outing3, self.outing2]]
        assert response_ids == outing_ids

    def test_get_sort_error(self):
        """Test failure of request (status 500) if an unknown
        keyword is used.
        """
        reset_search_index(self.session)
        self.get(self._prefix + "?sort=-elevation_axess", status=500)

    def test_get_version_without_activity(self):
        """Tests that old outings versions without activity include the fields
        of all activities.
        """
        self.outing_version.document_archive.activities = []
        self.session.flush()
        body = self.get_version(self.outing, self.outing_version)
        locale = body["document"]["locales"][0]
        assert "title" in locale

    def test_get_cooked(self):
        self.get_cooked(self.outing)

    def test_get_cooked_with_defaulting(self):
        self.get_cooked_with_defaulting(self.outing)

    def test_get_lang(self):
        self.get_lang(self.outing)

    def test_get_new_lang(self):
        self.get_new_lang(self.outing)

    def test_get_404(self):
        self.get_404()

    @pytest.mark.skip(reason="caching is handled and tested in flask-camp")
    def test_get_caching(self):
        self.get_caching(self.outing)

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info(self):
        body, locale = self.get_info(self.outing, "en")
        assert locale.get("lang") == "en"

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_best_lang(self):
        body, locale = self.get_info(self.outing, "es")
        assert locale.get("lang") == "fr"

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_404(self):
        self.get_info_404()

    @pytest.mark.skip(reason="useless test: empty payload...")
    def test_post_error(self):
        body = self.post_error({})
        errors = body.get("errors")
        assert len(errors) == 5
        self.assertCorniceRequired(self.get_error(errors, "activities"), "activities")
        self.assertCorniceRequired(self.get_error(errors, "date_end"), "date_end")
        self.assertCorniceRequired(self.get_error(errors, "date_start"), "date_start")
        self.assertError(errors, "associations.users", "at least one user required")
        self.assertError(errors, "associations.routes", "at least one route required")

    def test_post_empty_activities_error(self):
        body = self.post_error(
            {
                "activities": [],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "associations": {
                    "routes": [{"document_id": self.route.document_id}],
                    "users": [{"document_id": self.global_userids["contributor"]}],
                },
            }
        )
        errors = body.get("errors")
        assert len(errors) == 3
        error = self.get_error(errors, "activities")
        assert error.get("description") == "Shorter than minimum length 1"

    def test_post_invalid_activity(self):
        body_post = {
            "activities": ["cooking"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop"}],
            "associations": {
                "routes": [{"document_id": self.route.document_id}],
                "users": [{"document_id": self.global_userids["contributor"]}],
            },
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        assert errors[0].get("description") == "invalid value: cooking"
        assert errors[0].get("name") == "activities"

    def test_post_missing_title(self):
        body_post = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en"}],
            "associations": {
                "routes": [{"document_id": self.route.document_id}],
                "users": [{"document_id": self.global_userids["contributor"]}],
            },
        }
        body = self.post_missing_title(body_post)
        errors = body.get("errors")
        assert len(errors) == 3

    def test_post_date_start_is_tomorrow(self):
        later = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        body_post = {
            "activities": ["skitouring"],
            "date_start": later,
            "date_end": "2016-01-01",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "users": [
                    {"document_id": self.global_userids["contributor"]},
                    {"document_id": self.global_userids["contributor2"]},
                ],
                "routes": [{"document_id": self.route.document_id}],
                # images are ignored
                "images": [{"document_id": self.route.document_id}],
            },
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        assert errors[0]["name"] == "date_start"
        assert errors[0]["description"] == "can not be sometime in the future"

    def test_post_date_end_is_tomorrow(self):
        later = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        body_post = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": later,
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "users": [
                    {"document_id": self.global_userids["contributor"]},
                    {"document_id": self.global_userids["contributor2"]},
                ],
                "routes": [{"document_id": self.route.document_id}],
                # images are ignored
                "images": [{"document_id": self.route.document_id}],
            },
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        assert errors[0]["name"] == "date_end"
        assert errors[0]["description"] == "can not be sometime in the future"

    def test_post_end_date_is_prior_start_date(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        body_post = {
            "activities": ["skitouring"],
            "date_start": today.strftime("%Y-%m-%d"),
            "date_end": yesterday.strftime("%Y-%m-%d"),
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "users": [
                    {"document_id": self.global_userids["contributor"]},
                    {"document_id": self.global_userids["contributor2"]},
                ],
                "routes": [{"document_id": self.route.document_id}],
                # images are ignored
                "images": [{"document_id": self.route.document_id}],
            },
        }
        body = self.post_error(body_post)
        errors = body.get("errors")
        assert errors[0]["name"] == "date_end"
        assert errors[0]["description"] == "can not be prior the starting date"

    def test_post_non_whitelisted_attribute(self):
        body = {
            "activities": ["skitouring"],
            "protected": True,
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "routes": [{"document_id": self.route.document_id}],
                "users": [{"document_id": self.global_userids["contributor"]}],
            },
        }
        self.post_non_whitelisted_attribute(body)

    def test_post_missing_content_type(self):
        self.post_missing_content_type({})

    def test_post_missing_route_user_id(self):
        request_body = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                # missing route_id,
                "users": []
            },
        }
        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, headers=headers, status=400)

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("errors")
        assert len(errors) == 2
        self.assertError(errors, "associations.users", "at least one user required")
        self.assertError(errors, "associations.routes", "at least one route required")

    def test_post_invalid_route_id(self):
        request_body = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {"routes": [{"document_id": self.waypoint.document_id}], "users": [{"document_id": -999}]},
        }
        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, headers=headers, status=400)

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("errors")
        assert len(errors) == 4

        self.assertError(
            errors, "associations.routes", 'document "' + str(self.waypoint.document_id) + '" is not of type "r"'
        )
        self.assertError(errors, "associations.users", 'document "-999" does not exist or is redirected')
        self.assertError(errors, "associations.users", "at least one user required")
        self.assertError(errors, "associations.routes", "at least one route required")

    def test_post_success(self):
        body = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "geometry": {
                "id": 5678,
                "version": 6789,
                "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635966, 5723644]]}",
            },
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "users": [
                    {"document_id": self.global_userids["contributor"]},
                    {"document_id": self.global_userids["contributor2"]},
                ],
                "routes": [{"document_id": self.route.document_id}],
                # images are ignored
                "images": [{"document_id": self.route.document_id}],
            },
        }
        body, doc = self.post_success(body)
        self._assert_geometry(body)
        self._assert_default_geometry(body)
        assert doc.date_start == date(2016, 1, 1)
        assert doc.date_end == date(2016, 1, 2)

        version = doc.versions[0]

        archive_outing = version.document_archive
        assert archive_outing.activities == ["skitouring"]
        assert archive_outing.elevation_max == 1500

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Some nice loop"

        archive_geometry = version.document_geometry_archive
        assert archive_geometry.version == doc.geometry.version
        assert archive_geometry.geom_detail is not None

        association_route = self.session.query(Association).get((self.route.document_id, doc.document_id))
        assert association_route is not None

        association_route_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == self.route.document_id)
            .filter(AssociationLog.child_document_id == doc.document_id)
            .first()
        )
        assert association_route_log is not None

        association_user = self.session.query(Association).get((self.global_userids["contributor"], doc.document_id))
        assert association_user is not None

        association_user2 = self.session.query(Association).get((self.global_userids["contributor2"], doc.document_id))
        assert association_user2 is not None

        association_user_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == self.global_userids["contributor"])
            .filter(AssociationLog.child_document_id == doc.document_id)
            .first()
        )
        assert association_user_log is not None

        # check that a change is created in the feed
        feed_change = self.get_feed_change(doc.document_id)
        assert feed_change is not None
        assert feed_change.activities == ["skitouring"]
        self.assertEqual(
            feed_change.user_ids, [self.global_userids["contributor"], self.global_userids["contributor2"]]
        )
        self.assertEqual(feed_change.area_ids, [])

    def test_post_set_default_geom_from_route(self):
        body = {
            "activities": ["skitouring"],
            "date_start": "2016-01-01",
            "date_end": "2016-01-02",
            "elevation_min": 700,
            "elevation_max": 1500,
            "height_diff_up": 800,
            "height_diff_down": 800,
            "locales": [{"lang": "en", "title": "Some nice loop", "weather": "sunny"}],
            "associations": {
                "users": [{"document_id": self.global_userids["contributor"]}],
                "routes": [{"document_id": self.route.document_id}],
            },
        }
        body, doc = self.post_success(body)
        self._assert_default_geometry(body, x=635961, y=5723624)

    def test_put_wrong_document_id(self):
        body = {
            "document": {
                "document_id": "9999999",
                "version": self.outing.version,
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            }
        }
        self.put_wrong_document_id(body, user="moderator")

    def test_put_wrong_document_version(self):
        body = {
            "document": {
                "document_id": self.outing.document_id,
                "version": -9999,
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            }
        }
        self.put_wrong_version(body, self.outing.document_id, user="moderator")

    @pytest.mark.skip(reason="Locales are not versionned in the new model")
    def test_put_wrong_locale_version(self):
        body = {
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": -9999,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            }
        }
        self.put_wrong_version(body, self.outing.document_id, user="moderator")

    def test_put_wrong_ids(self):
        body = {
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            }
        }
        self.put_wrong_ids(body, self.outing.document_id, user="moderator")

    def test_put_no_document(self):
        self.put_put_no_document(self.outing.document_id)

    def test_put_wrong_user(self):
        """Test that a non-moderator user who is not associated to the outing
        is not allowed to modify.
        """
        body = {
            "message": "Update",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        headers = self.add_authorization_header(username="contributor2")
        self.app_put_json(self._prefix + "/" + str(self.outing.document_id), body, headers=headers, status=403)

    def test_put_good_user(self):
        """Test that a non-moderator user who is associated to the outing
        is allowed to modify.
        """
        body = {
            "message": "Update",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        headers = self.add_authorization_header(username="contributor")
        self.app_put_json(self._prefix + "/" + str(self.outing.document_id), body, headers=headers, status=200)

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring", "hiking"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-02",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.outing.geometry.version,
                    "geom_detail": '{"type": "LineString", "coordinates": ' + "[[635956, 5723604], [635976, 5723654]]}",
                },
                "associations": {
                    "users": [
                        {"document_id": self.global_userids["contributor"]},
                        {"document_id": self.global_userids["contributor2"]},
                    ],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        (body, outing) = self.put_success_all(body, self.outing, user="moderator", cache_version=3)

        # default geom is updated with the new track
        self._assert_default_geometry(body, x=635966, y=5723629)

        assert outing.elevation_max == 1600
        locale_en = outing.get_locale("en")
        assert locale_en.description == "..."
        assert locale_en.weather == "mostly sunny"

        # version with lang 'en'
        versions = outing.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "Mont Blanc from the air"
        assert archive_locale.weather == "mostly sunny"

        archive_document_en = version_en.document_archive
        assert archive_document_en.activities == ["skitouring", "hiking"]
        assert archive_document_en.elevation_max == 1600

        archive_geometry_en = version_en.document_geometry_archive
        assert archive_geometry_en.version == 2

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Mont Blanc du ciel"
        assert archive_locale.weather == "grand beau"

        # test that there are now 2 associated users
        association_user = self.session.query(Association).get((self.global_userids["contributor"], outing.document_id))
        assert association_user is not None
        association_user2 = self.session.query(Association).get(
            (self.global_userids["contributor2"], outing.document_id)
        )
        assert association_user2 is not None

        # check that the feed change is updated
        feed_change = self.get_feed_change(outing.document_id)
        assert feed_change is not None
        assert feed_change.activities == ["skitouring", "hiking"]
        self.assertEqual(feed_change.area_ids, [])
        self.assertEqual(
            feed_change.user_ids, [self.global_userids["contributor"], self.global_userids["contributor2"]]
        )

    def test_put_success_figures_only(self):
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-01",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        (body, route) = self.put_success_figures_only(body, self.outing, user="moderator")

        assert route.elevation_max == 1600

    def test_put_update_default_geom(self):
        """Tests that the default geometry can be updated directly."""
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-01",
                "elevation_min": 700,
                "elevation_max": 1600,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "geometry": {
                    "version": self.outing.geometry.version,
                    "geom": '{"type": "Point", "coordinates": [635000, 5723000]}',
                },
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        (body, route) = self.put_success_figures_only(body, self.outing, user="moderator")
        self._assert_default_geometry(body, x=635000, y=5723000)

    def test_put_success_lang_only(self):
        body = {
            "message": "Changing lang",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-01",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "elevation_access": 900,
                "condition_rating": "good",
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "mostly sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        (body, route) = self.put_success_lang_only(body, self.outing, user="moderator")

        assert route.get_locale("en").weather == "mostly sunny"

    def test_put_success_new_lang(self):
        """Test updating a document by adding a new locale."""
        body = {
            "message": "Adding lang",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-01",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "elevation_access": 900,
                "condition_rating": "good",
                "locales": [
                    {"lang": "es", "title": "Mont Blanc del cielo", "description": "...", "weather": "soleado"}
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }
        (body, route) = self.put_success_new_lang(body, self.outing, user="moderator")

        assert route.get_locale("es").weather == "soleado"

    def test_put_success_association_update(self):
        """Test updating a document by updating associations."""
        request_body = {
            "message": "Changing associations",
            "document": {
                "document_id": self.outing.document_id,
                "version": self.outing.version,
                "quality": quality_types[1],
                "activities": ["skitouring"],
                "date_start": "2016-01-01",
                "date_end": "2016-01-01",
                "elevation_min": 700,
                "elevation_max": 1500,
                "height_diff_up": 800,
                "height_diff_down": 800,
                "elevation_access": 900,
                "condition_rating": "good",
                "locales": [
                    {
                        "lang": "en",
                        "title": "Mont Blanc from the air",
                        "description": "...",
                        "weather": "sunny",
                        "version": self.locale_en.version,
                    }
                ],
                "associations": {
                    "users": [{"document_id": self.global_userids["contributor2"]}],
                    "routes": [{"document_id": self.route.document_id}],
                },
            },
        }

        headers = self.add_authorization_header(username="moderator")
        self.app_put_json(self._prefix + "/" + str(self.outing.document_id), request_body, headers=headers, status=200)

        response = self.get(self._prefix + "/" + str(self.outing.document_id), headers=headers, status=200)
        assert response.content_type == "application/json"

        body = response.json
        document_id = body.get("document_id")
        # document version does not change!
        assert body.get("version") == self.outing.version
        assert body.get("document_id") == document_id

        # check that the document was updated correctly
        self.session.expire_all()
        document = self.session.query(self._model).get(document_id)
        assert len(document.locales) == 2

        # check that no new archive_document was created
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
        assert archive_locale_count == 2

        self.assertNotifiedEs()

    def test_history(self):
        id = self.outing.document_id
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
        id = self.outing.document_id
        self.get("/document/%d/history/es" % id, status=404)

    def test_history_no_doc(self):
        self.get("/document/99999/history/es", status=404)

    @pytest.mark.skip(reason="This view is not relevant in new model")
    def test_get_associations_history(self):
        logs = self._get_association_logs(self.outing)

        assert len(logs) == 4

        # Third association (starting from the youngest) is a user
        log = logs[2]
        parent = log["parent_document"]
        assert parent["type"] == USERPROFILE_TYPE

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

    def _add_test_data(self):
        self.outing = Outing(
            activities=["skitouring"],
            date_start=date(2016, 1, 1),
            date_end=date(2016, 1, 1),
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            elevation_access=900,
            condition_rating="good",
        )
        self.locale_en = OutingLocale(
            lang="en",
            title="Mont Blanc from the air",
            description="...",
            weather="sunny",
            document_topic=DocumentTopic(topic_id=1),
        )

        self.locale_fr = OutingLocale(lang="fr", title="Mont Blanc du ciel", description="...", weather="grand beau")

        self.outing.locales.append(self.locale_en)
        self.outing.locales.append(self.locale_fr)

        self.outing.geometry = DocumentGeometry(
            geom_detail="SRID=3857;LINESTRING(635956 5723604, 635966 5723644)", geom="SRID=3857;POINT(635956 5723604)"
        )

        self.session_add(self.outing)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.outing, user_id)
        self.outing_version = self.session_query_first(DocumentVersion, document_id=self.outing.document_id)

        update_feed_document_create(self.outing, user_id)

        self.outing2 = Outing(
            activities=["skitouring"],
            date_start=date(2016, 2, 1),
            date_end=date(2016, 2, 1),
            height_diff_up=600,
            elevation_max=1800,
            elevation_access=700,
            condition_rating="average",
            locales=[OutingLocale(lang="en", title="Mont Blanc from the air", description="...", weather="sunny")],
            geometry=DocumentGeometry(geom="SRID=3857;POINT(0 0)"),
        )
        self.session_add(self.outing2)
        self.session.flush()
        DocumentRest.create_new_version(self.outing2, user_id)

        self.outing3 = Outing(
            activities=["skitouring"],
            date_start=date(2016, 2, 1),
            date_end=date(2016, 2, 2),
            height_diff_up=200,
            elevation_max=1200,
            elevation_access=800,
            condition_rating="poor",
        )
        self.session_add(self.outing3)
        self.outing4 = Outing(
            activities=["skitouring"],
            date_start=date(2016, 2, 1),
            date_end=date(2016, 2, 3),
            height_diff_up=500,
            elevation_max=1400,
            elevation_access=800,
            condition_rating="excellent",
        )
        self.outing4.locales.append(OutingLocale(lang="en", title="Mont Granier (en)", description="..."))
        self.outing4.locales.append(OutingLocale(lang="fr", title="Mont Granier (fr)", description="..."))
        self.session_add(self.outing4)

        self.waypoint = Waypoint(
            waypoint_type="summit", elevation=4, geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        )
        self.waypoint.locales.append(
            WaypointLocale(lang="en", title="Mont Granier (en)", description="...", access="yep")
        )
        self.waypoint.locales.append(
            WaypointLocale(lang="fr", title="Mont Granier (fr)", description="...", access="ouai")
        )
        self.session_add(self.waypoint)

        self.image = Image(
            filename="20160101-00:00:00.jpg", geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")
        )
        self.image.locales.append(DocumentLocale(lang="en", title="..."))
        self.session_add(self.image)

        self.article1 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article1)
        self.session.flush()

        # add some associations
        self.route = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=800,
            height_diff_down=800,
            durations="1",
            geometry=DocumentGeometry(
                geom_detail="SRID=3857;LINESTRING(635956 5723604, 635966 5723644)",  # noqa
                geom="SRID=3857;POINT(635961 5723624)",
            ),
        )
        self.route.locales.append(
            RouteLocale(
                lang="en",
                title="Mont Blanc from the air",
                description="...",
                gear="paraglider",
                title_prefix="Main waypoint title",
            )
        )
        self.route.locales.append(
            RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", gear="paraglider")
        )
        self.session_add(self.route)
        self.session.flush()

        self._add_association(
            Association.create(parent_document=self.waypoint, child_document=self.route), user_id=user_id
        )
        self._add_association(
            Association.create(parent_document=self.route, child_document=self.outing), user_id=user_id
        )

        self._add_association(
            Association(
                parent_document_id=user_id,
                parent_document_type=USERPROFILE_TYPE,
                child_document_id=self.outing.document_id,
                child_document_type=OUTING_TYPE,
            ),
            user_id=user_id,
        )
        self._add_association(
            Association.create(parent_document=self.outing, child_document=self.image), user_id=user_id
        )
        self._add_association(
            Association.create(parent_document=self.outing, child_document=self.article1), user_id=user_id
        )
        self.session.flush()
