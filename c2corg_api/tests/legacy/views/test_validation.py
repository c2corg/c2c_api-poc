import pytest

pytestmark = pytest.mark.skip("Not a views test")
from c2corg_api.legacy.models.outing import OUTING_TYPE
from c2corg_api.legacy.models.route import Route, ROUTE_TYPE
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.legacy.models.waypoint import Waypoint, WAYPOINT_TYPE
from c2corg_api.tests.legacy import BaseTestCase
from c2corg_api.legacy.views.validation import validate_associations_in, parse_datetime
from dateutil import parser as datetime_parser


class TestValidation(BaseTestCase):
    def setup_method(self):
        BaseTestCase.setup_method(self)

        self.waypoint1 = Waypoint(waypoint_type="summit")
        self.waypoint2 = Waypoint(waypoint_type="summit")
        self.route1 = Route(activities=["hiking"])
        self.route2 = Route(activities=["hiking"])
        self.user_profile1 = UserProfile()
        self.user_profile2 = UserProfile()
        self.session_add_all(
            [self.waypoint1, self.waypoint2, self.route1, self.route2, self.user_profile1, self.user_profile2]
        )
        self.session.flush()

    def test_validate_associations_outing(self):
        associations_in = {
            "routes": [{"document_id": self.route1.document_id}, {"document_id": self.route2.document_id}],
            "users": [{"document_id": self.user_profile1.document_id}],
            "waypoints": [{"document_id": "waypoints are ignored"}],
        }

        errors = Errors()
        associations = validate_associations_in(associations_in, OUTING_TYPE, errors)

        assert len(errors) == 0

        expected_associations = {
            "users": [{"document_id": self.user_profile1.document_id, "is_parent": True}],
            "routes": [
                {"document_id": self.route1.document_id, "is_parent": True},
                {"document_id": self.route2.document_id, "is_parent": True},
            ],
        }
        assert associations == expected_associations

    def test_validate_associations_waypoint(self):
        associations_in = {
            # routes are ignored
            "routes": [{"document_id": self.route1.document_id}],
            "waypoints": [{"document_id": self.waypoint1.document_id}],
            "waypoint_children": [{"document_id": self.waypoint2.document_id}],
            "outings": [{"document_id": "outings are ignored"}],
        }

        errors = Errors()
        associations = validate_associations_in(associations_in, WAYPOINT_TYPE, errors)

        assert len(errors) == 0

        expected_associations = {
            "waypoints": [{"document_id": self.waypoint1.document_id, "is_parent": True}],
            "waypoint_children": [{"document_id": self.waypoint2.document_id, "is_parent": False}],
        }
        assert associations == expected_associations

    def test_validate_associations_route(self):
        associations_in = {
            "routes": [{"document_id": self.route1.document_id}, {"document_id": self.route2.document_id}],
            "waypoints": [{"document_id": self.waypoint1.document_id}],
        }

        errors = Errors()
        associations = validate_associations_in(associations_in, ROUTE_TYPE, errors)

        assert len(errors) == 0

        expected_associations = {
            "routes": [
                {"document_id": self.route1.document_id, "is_parent": False},
                {"document_id": self.route2.document_id, "is_parent": False},
            ],
            "waypoints": [{"document_id": self.waypoint1.document_id, "is_parent": True}],
        }
        assert associations == expected_associations

    def test_validate_associations_invalid_type(self):
        associations_in = {"users": [{"document_id": self.user_profile1.document_id, "is_parent": True}]}

        errors = Errors()
        associations = validate_associations_in(associations_in, WAYPOINT_TYPE, errors)

        # users are ignored for waypoints
        assert associations == {}

    def test_validate_associations_invalid_document_id(self):
        associations_in = {"waypoints": [{"document_id": -99999}]}

        errors = Errors()
        associations = validate_associations_in(associations_in, WAYPOINT_TYPE, errors)

        assert associations is None
        error = errors[0]
        assert error["name"] == "associations.waypoints"
        assert error["description"] == 'document "-99999" does not exist or is redirected'

    def test_validate_associations_invalid_document_type(self):
        associations_in = {"routes": [{"document_id": self.waypoint1.document_id}]}

        errors = Errors()
        associations = validate_associations_in(associations_in, ROUTE_TYPE, errors)

        assert associations is None
        error = errors[0]
        assert error["name"] == "associations.routes"
        assert error["description"] == 'document "' + str(self.waypoint1.document_id) + '" is not of type "r"'

    def test_parse_datetime(self):
        assert parse_datetime(None) == None
        self.assertEqual(
            parse_datetime("2016-11-28T23:57:30.090459+01:00"),
            datetime_parser.parse("2016-11-28T23:57:30.090459+01:00"),
        )

        self.assertEqual(
            parse_datetime("2016-11-28T23%3A57%3A30.090459%2B01%3A00"),
            datetime_parser.parse("2016-11-28T23:57:30.090459+01:00"),
        )
