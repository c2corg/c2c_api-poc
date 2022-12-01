import pytest
from c2corg_api.legacy.models.document import DocumentGeometry, DocumentLocale
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.book import Book
from c2corg_api.legacy.models.route import Route, RouteLocale
from c2corg_api.legacy.models.waypoint import Waypoint, WaypointLocale
from c2corg_api.legacy.scripts.es.fill_index import fill_index
from c2corg_api.tests.legacy.search import force_search_index
from c2corg_api.tests.legacy.views import BaseTestRest


class TestSearchRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/search"

        self.article1 = Article(
            categories=["site_info"],
            activities=["hiking"],
            article_type="collab",
            locales=[
                DocumentLocale(lang="en", title="Lac d'Annecy", description="...", summary="Lac d'Annecy"),
                DocumentLocale(lang="en", title="Lac d'Annecy", description="...", summary="Lac d'Annecy"),
            ],
        )
        self.session_add(self.article1)
        self.waypoint1 = Waypoint(
            waypoint_type="summit",
            elevation=2000,
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
            locales=[
                WaypointLocale(lang="fr", title="Dent de Crolles", description="...", summary="La Dent de Crolles"),
                WaypointLocale(lang="en", title="Dent de Crolles", description="...", summary="The Dent de Crolles"),
            ],
        )
        self.session_add(self.waypoint1)
        self.session_add(
            Waypoint(
                waypoint_type="summit",
                elevation=4985,
                geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
                locales=[
                    WaypointLocale(
                        lang="en", title="Mont Blanc", description="...", summary="The heighest point in Europe"
                    )
                ],
            )
        )
        self.session_add(
            Route(
                activities=["skitouring"],
                elevation_max=1500,
                elevation_min=700,
                locales=[RouteLocale(lang="fr", title="Mont Blanc du ciel", description="...", summary="Ski")],
            )
        )
        self.book1 = Book(
            activities=["hiking"],
            book_types=["biography"],
            locales=[
                DocumentLocale(lang="en", title="Lac d'Annecy", description="...", summary="Lac d'Annecy"),
                DocumentLocale(lang="en", title="Lac d'Annecy", description="...", summary="Lac d'Annecy"),
            ],
        )
        self.session_add(self.book1)
        self.session.flush()
        fill_index(self.session)
        # make sure the search index is built
        force_search_index()

    def test_search(self):
        response = self.get(self._prefix + "?q=crolles", status=200)
        body = response.json

        assert "waypoints" in body
        assert "routes" in body
        assert "maps" in body
        assert "areas" in body
        assert "articles" in body
        assert "images" in body
        assert "outings" in body
        assert "books" in body

        waypoints = body["waypoints"]
        self.assertTrue(waypoints["total"] > 0)
        locales = waypoints["documents"][0]["locales"]
        assert len(locales) == 2
        assert "type" in waypoints["documents"][0]

        routes = body["routes"]
        assert 0 == len(routes["documents"])

        # tests that user results are not included when not authenticated
        assert "users" not in body

    def test_search_by_article_title(self):
        response = self.get(self._prefix + "?q=" + str(self.article1.locales[0].title), status=200)
        body = response.json
        articles = body["articles"]

        assert len(articles) == 2
        assert articles["total"] != 0

    def test_search_by_book_title(self):
        response = self.get(self._prefix + "?q=" + str(self.book1.locales[0].title), status=200)
        body = response.json
        books = body["books"]

        assert len(books) == 2
        assert books["total"] != 0

    def test_search_lang(self):
        response = self.get(self._prefix + "?q=crolles&pl=fr", status=200)
        body = response.json

        assert "waypoints" in body
        assert "routes" in body

        waypoints = body["waypoints"]
        self.assertTrue(waypoints["total"] > 0)

        locales = waypoints["documents"][0]["locales"]
        assert len(locales) == 1

    def test_search_authenticated(self):
        """Tests that user results are included when authenticated."""
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix + "?q=crolles", headers=headers, status=200)
        body = response.json

        assert "users" in body
        users = body["users"]
        assert "total" in users

    def test_search_user_unauthenticated(self):
        """Tests that user results are not included when not authenticated."""
        response = self.get(self._prefix + "?q=alex&t=u", status=200)
        body = response.json

        assert "users" not in body

    def test_search_limit_types(self):
        response = self.get(self._prefix + "?q=crolles&t=w,r,c,b", status=200)
        body = response.json

        assert "waypoints" in body
        assert "routes" in body
        assert "articles" in body
        assert "books" in body
        assert "maps" not in body
        assert "areas" not in body
        assert "images" not in body
        assert "outings" not in body
        assert "users" not in body

    @pytest.mark.xfail(reason="TODO")
    def test_search_by_document_id(self):
        response = self.get(self._prefix + "?q=" + str(self.waypoint1.document_id), status=200)
        body = response.json

        waypoints = body["waypoints"]
        assert len(waypoints["documents"]) == 1
        assert waypoints["total"] == 1

        routes = body["routes"]
        assert len(routes["documents"]) == 0
        assert routes["total"] == 0
