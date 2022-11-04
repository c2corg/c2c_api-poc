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

    def test_get_collection(self):
        body = self.get_collection()
        doc = body["documents"][0]
        assert "geometry" not in doc

    def test_get_collection_paginated(self):
        self.get("/books?offset=invalid", status=400)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 0}), [], 4)

        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 1}), [self.book4.document_id], 4)
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}), [self.book4.document_id, self.book3.document_id], 4
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 1, "limit": 2}), [self.book3.document_id, self.book2.document_id], 4
        )

    def test_get_collection_lang(self):
        self.get_collection_lang()

    def test_get_collection_search(self):
        reset_search_index(self.session)

        self.assertResultsEqual(
            self.get_collection_search({"l": "en"}), [self.book4.document_id, self.book1.document_id], 2
        )

        self.assertResultsEqual(
            self.get_collection_search({"btyp": ["biography"]}),
            [self.book4.document_id, self.book3.document_id, self.book2.document_id, self.book1.document_id],
            4,
        )

    def test_get(self):
        body = self.get_custom(self.book1)
        assert "book" not in body
        assert "geometry" not in body
        assert body.get("geometry") is None
        associations = body["associations"]

        assert "articles" in associations
        assert "images" in associations
        assert "routes" in associations
        assert "waypoints" in associations

        linked_routes = associations.get("routes")
        assert len(linked_routes) == 1

        linked_articles = associations.get("articles")
        assert len(linked_articles) == 0

        linked_images = associations.get("images")
        assert len(linked_images) == 0

    def test_get_cooked(self):
        self.get_cooked(self.book1)

    def test_get_cooked_with_defaulting(self):
        self.get_cooked_with_defaulting(self.book1)

    def test_get_lang(self):
        self.get_lang(self.book1)

    def test_get_new_lang(self):
        self.get_new_lang(self.book1)

    def test_get_404(self):
        self.get_404()

    def test_get_version(self):
        self.get_version(self.book1, self.book1_version)

    def test_get_version_etag(self):
        url = "{0}/{1}/en/{2}".format(self._prefix, str(self.book1.document_id), str(self.book1_version.id))
        response = self.get(url, status=200)

        # check that the ETag header is set
        headers = response.headers
        etag = headers.get("ETag")
        assert etag is not None

        # then request the document again with the etag
        headers = {"If-None-Match": etag}
        self.get(url, status=304, headers=headers)

    @pytest.mark.skip(reason="caching is handled and tested in flask-camp")
    def test_get_version_caching(self):
        url = "{0}/{1}/en/{2}".format(self._prefix, str(self.book1.document_id), str(self.book1_version.id))
        cache_key = "{0}-{1}".format(get_cache_key(self.book1.document_id, "en", BOOK_TYPE), self.book1_version.id)

        cache_value = cache_document_version.get(cache_key)
        assert cache_value == NO_VALUE

        # check that the response is cached
        self.get(url, status=200)

        cache_value = cache_document_version.get(cache_key)
        assert cache_value != NO_VALUE

        # check that values are returned from the cache
        fake_cache_value = {"document": "fake doc"}
        cache_document_version.set(cache_key, fake_cache_value)

        response = self.get(url, status=200)
        body = response.json
        assert body == fake_cache_value

    @pytest.mark.skip(reason="caching is handled and tested in flask-camp")
    def test_get_caching(self):
        self.get_caching(self.book1)

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info(self):
        body, locale = self.get_info(self.book1, "en")
        assert locale.get("lang") == "en"

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_best_lang(self):
        body, locale = self.get_info(self.book1, "es")
        assert locale.get("lang") == "fr"

    @pytest.mark.skip(reason="test_get_info is not used in UI")
    def test_get_info_404(self):
        self.get_info_404()

    @pytest.mark.skip(reason="useless test: empty payload...")
    def test_post_error(self):
        body = self.post_error({}, user="moderator")
        errors = body.get("errors")
        assert len(errors) == 2
        self.assertCorniceRequired(errors[0], "locales")

    def test_post_missing_title(self):
        body_post = {"activities": ["hiking"], "book_types": ["biography"], "locales": [{"lang": "en"}]}
        self.post_missing_title(body_post, user="moderator")

    def test_post_non_whitelisted_attribute(self):
        body = {
            "book_types": ["biography"],
            "protected": True,
            "locales": [{"lang": "en", "title": "Escalades au Thaurac"}],
        }
        self.post_non_whitelisted_attribute(body, user="moderator")

    def test_post_missing_content_type(self):
        self.post_missing_content_type({})

    @pytest.mark.skip(reason="Rewritted without the part on associations, as it does not exists in the mew model")
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

        # check that a link to the associated waypoint is created
        association_wp = self.session.query(Association).get((doc.document_id, self.waypoint2.document_id))
        assert association_wp is not None

        association_wp_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == doc.document_id)
            .filter(AssociationLog.child_document_id == self.waypoint2.document_id)
            .first()
        )
        assert association_wp_log is not None

        # check that a link to the associated article is created
        association_art = self.session.query(Association).get((doc.document_id, self.article2.document_id))
        assert association_art is not None

        association_art_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == doc.document_id)
            .filter(AssociationLog.child_document_id == self.article2.document_id)
            .first()
        )
        assert association_art_log is not None

    def test_put_wrong_document_id(self):
        body = {
            "document": {
                "document_id": "9999999",
                "version": self.book1.version,
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "en", "title": "Escalades au Thaurac", "version": self.locale_en.version}],
            }
        }
        self.put_wrong_document_id(body, user="moderator")

    def test_put_wrong_document_version(self):
        body = {
            "document": {
                "document_id": self.book1.document_id,
                "version": -9999,
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "en", "title": "Escalades au Thaurac", "version": self.locale_en.version}],
            }
        }
        self.put_wrong_version(body, self.book1.document_id, user="moderator")

    def test_put_wrong_locale_version(self):
        body = {
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "en", "title": "Escalades au Thaurac", "version": -9999}],
            }
        }
        self.put_wrong_version(body, self.book1.document_id, user="moderator")

    def test_put_wrong_ids(self):
        body = {
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "en", "title": "Escalades au Thaurac", "version": self.locale_en.version}],
            }
        }
        self.put_wrong_ids(body, self.book1.document_id, user="moderator")

    def test_put_no_document(self):
        self.put_put_no_document(self.book1.document_id, user="moderator")

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

        # check that a link to the associated image is created
        association_img = self.session.query(Association).get((book1.document_id, self.image2.document_id))
        assert association_img is not None

        association_img_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == book1.document_id)
            .filter(AssociationLog.child_document_id == self.image2.document_id)
            .first()
        )
        assert association_img_log is not None

        # check that a link to the associated route is created
        association_rou = self.session.query(Association).get((book1.document_id, self.route2.document_id))
        assert association_rou is not None

        association_rou_log = (
            self.session.query(AssociationLog)
            .filter(AssociationLog.parent_document_id == book1.document_id)
            .filter(AssociationLog.child_document_id == self.route2.document_id)
            .first()
        )
        assert association_rou_log is not None

    def test_put_success_figures_only(self):
        body = {
            "message": "Changing figures",
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "quality": quality_types[1],
                "activities": ["hiking"],
                "book_types": ["biography"],
                "author": "New author",
                "editor": "New editor",
            },
        }
        (body, book1) = self.put_success_figures_only(body, self.book1, user="moderator")

        assert book1.activities == ["hiking"]
        assert book1.book_types == ["biography"]

    def test_put_success_lang_only(self):
        body = {
            "message": "Changing lang",
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "quality": quality_types[1],
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "en", "title": "New title", "version": self.locale_en.version}],
            },
        }
        (body, book1) = self.put_success_lang_only(body, self.book1, user="moderator")

        assert book1.get_locale("en").title == "New title"

    def test_put_success_new_lang(self):
        """Test updating a document by adding a new locale."""
        body = {
            "message": "Adding lang",
            "document": {
                "document_id": self.book1.document_id,
                "version": self.book1.version,
                "quality": quality_types[1],
                "activities": ["hiking"],
                "book_types": ["biography"],
                "locales": [{"lang": "es", "title": "Escalades au Thaurac"}],
            },
        }
        (body, book1) = self.put_success_new_lang(body, self.book1, user="moderator")

        assert book1.get_locale("es").title == "Escalades au Thaurac"

    def test_get_associations_history(self):
        self._get_association_logs(self.book1)

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
