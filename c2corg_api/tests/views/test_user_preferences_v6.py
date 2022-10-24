from copy import deepcopy
from unittest.mock import patch

from flask_camp.models import Document

from c2corg_api.tests.conftest import BaseTestClass


class TestUserFilterPreferencesRest(BaseTestClass):
    def test_post_preferences_invalid(self, user):
        self.login_user(user)

        base_data = {"followed_only": True, "activities": ["hiking"], "langs": ["fr"], "areas": []}

        data = deepcopy(base_data)
        del data["followed_only"]
        self.post("/users/preferences", prefix="", json=data, status=400)

        data = deepcopy(base_data)
        data["activities"] = ["hiking", "soccer"]
        self.post("/users/preferences", prefix="", json=data, status=400)

        data = deepcopy(base_data)
        data["langs"] = ["fr", "xx"]
        self.post("/users/preferences", prefix="", json=data, status=400)

        data = deepcopy(base_data)
        data["areas"] = [{"id": 42}]
        self.post("/users/preferences", prefix="", json=data, status=400)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_post_preferences(self, sync_sso, user):
        area = Document.create("Creation", {"locales": []}, author=user)
        self.api.database.session.add(area)
        self.api.database.session.commit()

        self.login_user(user)

        request_body = {
            "followed_only": True,
            "activities": ["hiking", "skitouring"],
            "langs": ["fr", "en"],
            "areas": [{"document_id": area.id}],
        }

        self.post("/users/preferences", prefix="", json=request_body, status=200)
        preferences = self.get_current_user().json["user"]["ui_preferences"]

        assert preferences["feed"]["followed_only"] is True
        assert preferences["feed"]["activities"] == ["hiking", "skitouring"]
        assert preferences["feed"]["langs"] == ["fr", "en"]
