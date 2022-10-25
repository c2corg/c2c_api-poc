from copy import deepcopy
from unittest.mock import patch

from flask_camp.models import Document, User

from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.models.area import Area


class TestUserFilterPreferencesRest(BaseTestRest):
    def test_post_preferences_invalid(self):
        self.optimized_login("contributor")

        base_data = {"followed_only": True, "activities": ["hiking"], "langs": ["fr"], "areas": [], "follow": []}

        data = deepcopy(base_data)
        del data["followed_only"]
        self.post("/users/preferences", json=data, status=400)

        data = deepcopy(base_data)
        data["activities"] = ["hiking", "soccer"]
        self.post("/users/preferences", json=data, status=400)

        data = deepcopy(base_data)
        data["langs"] = ["fr", "xx"]
        self.post("/users/preferences", json=data, status=400)

        data = deepcopy(base_data)
        data["areas"] = [{"id": 42}]
        self.post("/users/preferences", json=data, status=400)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_post_preferences(self, sync_sso):

        area = Area("country", locales=[])._document
        self.api.database.session.add(area)
        self.api.database.session.commit()

        self.optimized_login("contributor")

        request_body = {
            "followed_only": True,
            "activities": ["hiking", "skitouring"],
            "langs": ["fr", "en"],
            "areas": [{"document_id": area.id}],
            "follow": [],
        }

        self.post("/users/preferences", json=request_body, status=200)
        preferences = self.get("/v7/current_user").json["user"]["ui_preferences"]

        assert preferences["feed"]["followed_only"] is True
        assert preferences["feed"]["activities"] == ["hiking", "skitouring"]
        assert preferences["feed"]["langs"] == ["fr", "en"]
