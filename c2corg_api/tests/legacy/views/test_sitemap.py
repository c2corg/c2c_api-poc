import pytest
from c2corg_api.legacy.models.route import RouteLocale, Route
from c2corg_api.legacy.models.waypoint import WaypointLocale, Waypoint

from c2corg_api.tests.legacy.views import BaseTestRest


class TestSitemapRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/sitemaps"

        self.waypoint1 = Waypoint(
            waypoint_type="summit", elevation=2000, locales=[WaypointLocale(lang="fr", title="Dent de Crolles")]
        )
        self.session_add(self.waypoint1)
        self.waypoint2 = Waypoint(
            waypoint_type="summit",
            elevation=4985,
            locales=[WaypointLocale(lang="en", title="Mont Blanc"), WaypointLocale(lang="fr", title="Mont Blanc")],
        )
        self.session_add(self.waypoint2)
        self.route = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            main_waypoint_id=self.waypoint2.document_id,
            locales=[RouteLocale(lang="fr", title="Mont Blanc du ciel", title_prefix="Mont Blanc")],
        )
        self.session_add(self.route)
        self.session.flush()

    def test_get(self):
        response = self.get(self._prefix, status=200)
        body = response.json

        sitemaps = body["sitemaps"]
        self.assertIsNotNone(next(filter(lambda s: s["url"] == "/sitemaps/waypoint/0", sitemaps), None))
        self.assertIsNotNone(next(filter(lambda s: s["url"] == "/sitemaps/route/0", sitemaps), None))

    def test_get_sitemap_invalid_doc_type(self):
        response = self.get(self._prefix + "/z/0", status=400)
        errors = response.json["description"]
        assert "Invalid document type" in errors

    def test_get_sitemap_invalid_page(self):
        response = self.get(self._prefix + "/area/-123", status=404)
        # errors = response.json["errors"]
        # self.assertError(errors, "i", "invalid i")

    def test_get_waypoint_sitemap(self):
        response = self.get(self._prefix + "/waypoint/0", status=200)
        body = response.json

        pages = body["pages"]
        assert len(pages) == 3
        page1 = pages[0]
        assert self.waypoint1.document_id == page1["document_id"]
        assert "title" in page1
        assert "lang" in page1
        assert "lastmod" in page1

    @pytest.mark.skip(reason="Simple 200 with empty response")
    def test_get_waypoint_sitemap_no_pages(self):
        self.get(self._prefix + "/waypoint/1", status=404)

    def test_get_route_sitemap(self):
        response = self.get(self._prefix + "/route/0", status=200)
        body = response.json

        pages = body["pages"]
        assert len(pages) == 1
        page1 = pages[0]
        assert self.route.document_id == page1["document_id"]
        assert "title" in page1
        assert "title_prefix" in page1
        assert "lang" in page1
        assert "lastmod" in page1
