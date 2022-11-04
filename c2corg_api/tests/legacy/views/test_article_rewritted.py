import pytest
from c2corg_api.legacy.caching import cache_document_version
from c2corg_api.legacy.models.article import ArchiveArticle, Article, ARTICLE_TYPE
from c2corg_api.legacy.models.association import AssociationLog, Association
from c2corg_api.legacy.models.cache_version import get_cache_key
from c2corg_api.legacy.models.document_history import DocumentVersion
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.tests.legacy.search import reset_search_index

from c2corg_api.legacy.models.document import ArchiveDocumentLocale, DocumentLocale, DocumentGeometry
from c2corg_api.legacy.views.document import DocumentRest

from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from c2corg_api.models.common.attributes import quality_types

# from dogpile.cache.api import NO_VALUE


class TestArticleRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/articles", ARTICLE_TYPE, Article, ArchiveArticle, ArchiveDocumentLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()
        self.session.commit()

    def test_post_success(self):
        body = {
            "document_id": 123456,
            "version": 567890,
            "categories": ["site_info"],
            "activities": ["hiking"],
            "article_type": "collab",
            "associations": {
                "waypoints": [{"document_id": self.waypoint2.document_id}],
                "articles": [{"document_id": self.article2.document_id}],
            },
            "geometry": {
                "version": 1,
                "document_id": self.waypoint2.document_id,
                "geom": '{"type": "Point", "coordinates": [635956, 5723604]}',
            },
            "locales": [{"lang": "en", "title": "Lac d'Annecy"}],
        }
        body, doc = self.post_success(body, user="moderator")
        version = doc.versions[0]

        archive_article = version.document_archive
        assert archive_article.categories == ["site_info"]
        assert archive_article.activities == ["hiking"]
        assert archive_article.article_type == "collab"

        archive_locale = version.document_locales_archive
        assert archive_locale.lang == "en"
        assert archive_locale.title == "Lac d'Annecy"

        # check if geometry is not stored in database afterwards
        assert doc.geometry is None

    def test_put_success_all(self):
        body = {
            "message": "Update",
            "document": {
                "document_id": self.article1.document_id,
                "version": self.article1.version,
                "quality": quality_types[1],
                "categories": ["site_info"],
                "activities": ["hiking"],
                "article_type": "personal",
                "associations": {
                    "waypoints": [{"document_id": self.waypoint2.document_id}],
                    "articles": [{"document_id": self.article2.document_id}],
                    "images": [],
                },
                "geometry": {"geom": '{"type": "Point", "coordinates": [635956, 5723604]}'},
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }
        (body, article1) = self.put_success_all(body, self.article1, user="moderator", cache_version=3)

        assert article1.activities == ["hiking"]
        locale_en = article1.get_locale("en")
        assert locale_en.title == "New title"

        # version with lang 'en'
        versions = article1.versions
        version_en = self.get_latest_version("en", versions)
        archive_locale = version_en.document_locales_archive
        assert archive_locale.title == "New title"

        archive_document_en = version_en.document_archive
        assert archive_document_en.categories == ["site_info"]
        assert archive_document_en.activities == ["hiking"]
        assert archive_document_en.article_type == "personal"

        # version with lang 'fr'
        version_fr = self.get_latest_version("fr", versions)
        archive_locale = version_fr.document_locales_archive
        assert archive_locale.title == "Lac d'Annecy"

        # check if geometry is not stored in database afterwards
        assert article1.geometry is None

    def _add_test_data(self):
        self.article1 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.locale_en = DocumentLocale(lang="en", title="Lac d'Annecy")
        self.locale_fr = DocumentLocale(lang="fr", title="Lac d'Annecy")

        self.article1.locales.append(self.locale_en)
        self.article1.locales.append(self.locale_fr)

        self.session_add(self.article1)
        self.session.flush()

        user_id = self.global_userids["contributor"]
        DocumentRest.create_new_version(self.article1, user_id)
        self.article1_version = self.session_query_first(DocumentVersion, document_id=self.article1.document_id)

        self.article2 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article2)
        self.article3 = Article(categories=["site_info"], activities=["hiking"], article_type="collab")
        self.session_add(self.article3)
        self.article4 = Article(categories=["site_info"], activities=["hiking"], article_type="personal")
        self.article4.locales.append(DocumentLocale(lang="en", title="Lac d'Annecy"))
        self.article4.locales.append(DocumentLocale(lang="fr", title="Lac d'Annecy"))
        self.session_add(self.article4)
        self.session.flush()

        DocumentRest.create_new_version(self.article4, user_id)
        self.article4_version = self.session_query_first(DocumentVersion, document_id=self.article4.document_id)

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

        self._add_association(Association.create(parent_document=self.article1, child_document=self.article4), user_id)
        self._add_association(Association.create(parent_document=self.article3, child_document=self.article1), user_id)
        self.session.flush()
