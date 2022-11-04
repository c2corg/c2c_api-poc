import pytest
from c2corg_api.legacy.caching import cache_document_version
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.book import ArchiveBook, Book, BOOK_TYPE
from c2corg_api.legacy.models.association import AssociationLog, Association
from c2corg_api.legacy.models.cache_version import get_cache_key
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.document_topic import DocumentTopic
from c2corg_api.legacy.models.route import Route, RouteLocale
from c2corg_api.legacy.models.image import Image
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.tests.legacy.search import reset_search_index

from c2corg_api.legacy.models.document import ArchiveDocumentLocale, DocumentLocale, DocumentGeometry
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from c2corg_api.models.common.attributes import quality_types

# from dogpile.cache.api import NO_VALUE


class TestBookRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/books", BOOK_TYPE, Book, ArchiveBook, ArchiveDocumentLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_post_success(self):
        body = {
            "document_id": 12345678,
            "version": 98765432,
            "activities": ["hiking"],
            "book_types": ["biography"],
            "author": "NewAuthor",
            "editor": "NewEditor",
            "isbn": "12345678",
            "nb_pages": 150,
            "publication_date": "1984",
            "url": "http://www.nowhere.to.find",
            "associations": {
                "waypoints": [{"document_id": self.waypoint2.document_id}],
                "articles": [{"document_id": self.article2.document_id}],
            },
            "geometry": {
                "version": 1,
                "document_id": self.waypoint2.document_id,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "locales": [{"lang": "en", "title": "Escalades au Thaurac"}],
        }
        body, doc = self.post_success(body, user="moderator")
        version = doc.versions[0]

        archive_book = version.document_archive
        assert archive_book.activities == ["hiking"]
        assert archive_book.book_types == ["biography"]

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Escalades au Thaurac"

        # check if geometry is not stored in database afterwards
        assert doc.geometry is None

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "quality": quality_types[1],
                "activities": ["hiking"],
                "book_types": ["magazine"],
                "associations": {
                    "articles": [{"document_id": self.article2.document_id}],
                    "images": [{"document_id": self.image2.document_id}],
                    "routes": [{"document_id": self.route2.document_id}],
                },
                "geometry": {
                    "version": 1,
                    "document_id": self.waypoint2.document_id,
                    "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
                },
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }

        (body, book1) = self.put_success_all(body, self.book1, user="moderator", cache_version=3)

        assert book1.activities == ["hiking"]
        locale_en = book1.get_locale("en")
        assert locale_en.title == "New title"

        # version with lang 'en'
        versions = book1.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "New title"

        archive_document_en = version_en.document_archive
        assert archive_document_en.activities == ["hiking"]
        assert archive_document_en.book_types == ["magazine"]

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Escalades au Thaurac"

        # check if geometry is not stored in database afterwards
        assert book1.geometry is None

    def _add_test_data(self):
        self.book1 = Book(activities=["hiking"], book_types=["biography"])
        self.locale_en = DocumentLocale(lang="en", title="Escalades au Thaurac")
        self.locale_fr = DocumentLocale(lang="fr", title="Escalades au Thaurac")

        self.book1.locales.append(self.locale_en)
        self.book1.locales.append(self.locale_fr)

        self.session_add(self.book1)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.book1, user_id)
        self.book1_version = self.session_query_first(DocumentVersion, document_id=self.book1.document_id)

        self.book2 = Book(activities=["hiking"], book_types=["biography"])
        self.session_add(self.book2)
        self.book3 = Book(activities=["hiking"], book_types=["biography"])
        self.session_add(self.book3)
        self.book4 = Book(activities=["hiking"], book_types=["biography"])
        self.book4.locales.append(DocumentLocale(lang="en", title="Escalades au Thaurac"))
        self.book4.locales.append(DocumentLocale(lang="fr", title="Escalades au Thaurac"))
        self.session_add(self.book4)
        self.waypoint1 = Waypoint(waypoint_type="summit", elevation=2203)
        self.session_add(self.waypoint1)
        self.waypoint2 = Waypoint(
            waypoint_type="climbing_outdoor",
            elevation=2,
            rock_types=[],
            geometry=DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)"),
        )
        self.session_add(self.waypoint2)
        self.session.flush()

        self.article2 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article2)
        self.session.flush()

        self.image = Image(filename="image.jpg", activities=["paragliding"], height=1500, image_type="collaborative")

        self.locale_en_img = DocumentLocale(
            lang="en", title="Mont Blanc from the air", description="...", document_topic=DocumentTopic(topic_id=1)
        )

        self.locale_fr_img = DocumentLocale(lang="fr", title="Mont Blanc du ciel", description="...")

        self.image.locales.append(self.locale_en_img)
        self.image.locales.append(self.locale_fr_img)

        self.image.geometry = DocumentGeometry(geom="SRID=3857;POINT(635956 5723604)")

        self.session_add(self.image)
        self.session.flush()

        self.image2 = Image(filename="image2.jpg", activities=["paragliding"], height=1500)
        self.session_add(self.image2)
        self.session.flush()

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

        self.route3 = Route(
            activities=["skitouring"],
            elevation_max=1500,
            elevation_min=700,
            height_diff_up=500,
            height_diff_down=500,
            durations="1",
        )
        self.session_add(self.route3)
        self.session.flush()

        # self._add_association(Association.create(
        #     parent_document=self.book1,
        #     child_document=self.image2), user_id)
        self._add_association(Association.create(parent_document=self.book1, child_document=self.route3), user_id)
        self._add_association(Association.create(parent_document=self.book2, child_document=self.waypoint2), user_id)
        self.session.flush()
