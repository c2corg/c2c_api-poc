import pytest
from c2corg_api.legacy.models.route import RouteLocale, Route
from c2corg_api.legacy.models.waypoint import WaypointLocale, Waypoint

from c2corg_api.tests.legacy.views import BaseTestRest


class TestSitemapXml(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/sitemaps.xml"
        self.ui_url = "https://www.camptocamp.org"
        self.schema_url = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

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
        from xml.etree import ElementTree

        sitemaps = ElementTree.fromstring(response.data)

        base_url = "https://api.camptocamp.org/sitemaps.xml"

        def waypoint_filter(s):
            return s[0].text == base_url + "/waypoint/0.xml"

        def route_filter(s):
            return s[0].text == base_url + "/route/0.xml"

        self.assertIsNotNone(next(filter(waypoint_filter, sitemaps), None))
        self.assertIsNotNone(next(filter(route_filter, sitemaps), None))

    def test_get_sitemap_invalid_doc_type(self):
        response = self.get(self._prefix + "/z/0.xml", status=400)
        errors = response.json["description"]
        assert "Invalid document type" in errors

    def test_get_sitemap_invalid_page(self):
        response = self.get(self._prefix + "/area/-123.xml", status=404)
        # errors = response.json["errors"]
        # self.assertError(errors, "i", "invalid i")

    def test_get_waypoint_sitemap(self):
        response = self.get(self._prefix + "/waypoint/0.xml", status=200)
        from xml.etree import ElementTree

        urlset = ElementTree.fromstring(response.data)

        assert len(urlset) == 3
        url = urlset[0]

        self.assertEqual(url[0].tag, "{}loc".format(self.schema_url))
        self.assertEqual(url[1].tag, "{}lastmod".format(self.schema_url))
        self.assertEqual(
            url[0].text, "{}/waypoint/{}/fr/dent-de-crolles".format(self.ui_url, self.waypoint1.document_id)
        )

    @pytest.mark.skip(reason="Simple 200 with empty response")
    def test_get_waypoint_sitemap_no_pages(self):
        self.get(self._prefix + "/waypoint/1.xml", status=404)

    def test_get_route_sitemap(self):
        response = self.get(self._prefix + "/route/0.xml", status=200)
        from xml.etree import ElementTree

        urlset = ElementTree.fromstring(response.data)

        assert len(urlset) == 1
        url = urlset[0]

        self.assertEqual(url[0].tag, "{}loc".format(self.schema_url))
        self.assertEqual(url[1].tag, "{}lastmod".format(self.schema_url))
        self.assertEqual(
            url[0].text, "{}/route/{}/fr/mont-blanc-mont-blanc-du-ciel".format(self.ui_url, self.route.document_id)
        )
