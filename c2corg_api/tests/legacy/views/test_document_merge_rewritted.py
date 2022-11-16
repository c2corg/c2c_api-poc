from c2corg_api.legacy.models.association import Association
from c2corg_api.legacy.models.document import DocumentGeometry
from c2corg_api.legacy.models.document_tag import DocumentTag
from c2corg_api.legacy.models.route import Route, RouteLocale, ROUTE_TYPE
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.views.document import DocumentRest


class TestDocumentMergeRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/documents/merge"

        contributor_id = self.global_userids["contributor"]

        self.waypoint1 = Waypoint(
            waypoint_type="summit",
            elevation=2000,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
            locales=[
                WaypointLocale(lang="fr", title="Dent de Crolles", description="...", summary="La Dent de Crolles")
            ],
        )
        self.session_add(self.waypoint1)
        self.waypoint2 = Waypoint(
            waypoint_type="summit",
            elevation=4985,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
            locales=[
                WaypointLocale(lang="en", title="Mont Blanc", description="...", summary="The heighest point in Europe")
            ],
        )
        self.session_add(self.waypoint2)
        self.session.flush()
        self.waypoint3 = Waypoint(
            waypoint_type="summit",
            elevation=4985,
            redirects_to=self.waypoint1.document_id,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
            locales=[
                WaypointLocale(lang="en", title="Mont Blanc", description="...", summary="The heighest point in Europe")
            ],
        )
        self.session_add(self.waypoint3)
        self.waypoint4 = Waypoint(
            waypoint_type="summit",
            elevation=4985,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
            locales=[
                WaypointLocale(lang="en", title="Mont Blanc", description="...", summary="The heighest point in Europe")
            ],
        )
        self.session_add(self.waypoint4)
        self.session.flush()

        self.route1 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            main_waypoint_id=self.waypoint1.document_id,
            locales=[RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", summary="Ski")],
        )
        self.session_add(self.route1)

        self.route2 = Route(
            activities=["skitouring"],
            elevation_max=1400,
            elevation_min=700,
            main_waypoint_id=self.waypoint1.document_id,
            locales=[RouteLocale(lang="fr", title="Mont Blanc du soleil", description="...", summary="Ski")],
        )
        self.session_add(self.route2)
        self.session.flush()

        DocumentRest.create_new_version(self.waypoint1, contributor_id)
        DocumentRest.create_new_version(self.route1, contributor_id)
        DocumentRest.create_new_version(self.route2, contributor_id)

        association = Association.create(parent_document=self.waypoint1, child_document=self.route1)
        self.session_add(association)
        self.session_add(association.get_log(self.global_userids["contributor"]))

        association = Association.create(parent_document=self.waypoint1, child_document=self.route2)
        self.session_add(association)
        self.session_add(association.get_log(self.global_userids["contributor"]))

        association = Association.create(parent_document=self.waypoint1, child_document=self.waypoint4)
        self.session_add(association)
        self.session_add(association.get_log(self.global_userids["contributor"]))

        association = Association.create(parent_document=self.waypoint2, child_document=self.waypoint4)
        self.session_add(association)
        self.session_add(association.get_log(self.global_userids["contributor"]))
        self.session.flush()

        self.session_add(
            DocumentTag(document_id=self.route1.document_id, document_type=ROUTE_TYPE, user_id=contributor_id)
        )
        self.session.commit()

        self.waypoint1 = self.get(f"/v7/document/{self.waypoint1.document_id}").json["document"]
        self.waypoint2 = self.get(f"/v7/document/{self.waypoint2.document_id}").json["document"]
        self.waypoint3 = self.get(f"/v7/document/{self.waypoint3.document_id}", status=301).json["document"]
        self.waypoint4 = self.get(f"/v7/document/{self.waypoint4.document_id}").json["document"]
        self.route1 = self.get(f"/v7/document/{self.route1.document_id}").json["document"]
        self.route2 = self.get(f"/v7/document/{self.route2.document_id}").json["document"]

    def _post(self, body, expected_status):
        headers = self.add_authorization_header(username="moderator")
        return self.app_post_json(self._prefix, body, headers=headers, status=expected_status)

    def test_already_merged(self):
        self._post({"source_document_id": self.waypoint3["id"], "target_document_id": self.waypoint2["id"]}, 400)
        self._post({"source_document_id": self.waypoint2["id"], "target_document_id": self.waypoint3["id"]}, 400)

    def test_merge_waypoint(self):
        self._post({"source_document_id": self.waypoint1["id"], "target_document_id": self.waypoint2["id"]}, 200)

        route = self.get(f"/v7/document/{self.route1['id']}").json["document"]
        assert route["data"]["main_waypoint_id"] == self.waypoint1["id"]
        assert route["cooked_data"]["associations"]["waypoint"][str(self.waypoint1["id"])]["id"] == self.waypoint2["id"]

        route_locale = route["cooked_data"]["locales"]["fr"]
        assert route_locale["title_prefix"] == "Mont Blanc"

        waypoint = self.get(f"/v7/document/{self.waypoint1['id']}", status=301).json["document"]
        assert waypoint["redirects_to"] == self.waypoint2["id"]

    def test_tags(self):
        tags = self.get("/v7/tags").json["tags"]
        assert len(tags) == 1
        assert tags[0]["document_id"] == self.route1["id"]

        self._post({"source_document_id": self.route1["id"], "target_document_id": self.route2["id"]}, 200)

        tags = self.get("/v7/tags").json["tags"]
        assert len(tags) == 1
        assert tags[0]["document_id"] == self.route2["id"]
