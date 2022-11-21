# import functools
# from datetime import date
import json
import logging
from math import ceil

from flask import Response, request
from flask_camp import current_api, allow
from sqlalchemy.sql.functions import func

from werkzeug.exceptions import BadRequest

# from c2corg_api.models.document import Document, DocumentLocale
# from c2corg_api.models.route import RouteLocale
from c2corg_api.search import DocumentSearch
from c2corg_api.models import USERPROFILE_TYPE, ROUTE_TYPE, models as document_types


log = logging.getLogger(__name__)

# Search engines accept not more than 50000 urls per sitemap,
# and the sitemap files may not exceed 10 MB. With 50000 urls the sitemaps
# are not bigger than 9MB, but to be safe we are using 45000 urls per sitemap.
# see http://www.sitemaps.org/protocol.html
PAGES_PER_SITEMAP = 45000


class Sitemaps(object):
    rule = "/sitemaps"

    @allow("anonymous")
    def get(self):

        """Returns the information needed to generate a sitemap index file.
        See: http://www.sitemaps.org/protocol.html

        The response consists of a list of URLs to request the information
        needed to generate the sitemap linked from the sitemap index.

        E.g.

            {
                "sitemaps": [
                    "/sitemaps/w/0",
                    "/sitemaps/a/0",
                    "/sitemaps/i/0",
                    "/sitemaps/i/1",
                    "/sitemaps/i/2",
                    "/sitemaps/i/3",
                    "/sitemaps/i/4",
                    "/sitemaps/i/5",
                    ...
                ]
            }
        """

        document_locales_per_type = (
            current_api.database.session.query(
                DocumentSearch.document_type,
                func.sum(func.array_length(DocumentSearch.available_langs, 1)).label("count"),
            )
            .filter(DocumentSearch.document_type != USERPROFILE_TYPE)
            .group_by(DocumentSearch.document_type)
            .all()
        )

        sitemaps = []
        for doc_type, count in document_locales_per_type:
            num_sitemaps = ceil(count / PAGES_PER_SITEMAP)
            sitemaps += [
                {"url": f"/sitemaps/{doc_type}/{i}", "doc_type": doc_type, "i": i} for i in range(0, num_sitemaps)
            ]

        result = Response(response=json.dumps({"sitemaps": sitemaps}), content_type="application/json")
        result.add_etag()  # TODO : compute it only one time per day
        result.make_conditional(request)

        return result


class Sitemap(object):
    rule = "/sitemaps/<string:document_type>/<int:page>"

    @allow("anonymous")
    def get(self, document_type, page):
        """Returns the information needed to generate a sitemap for a given
        type and sitemap page number.
        """

        if document_type not in document_types:
            raise BadRequest("Invalid document type")

        return {}


#         doc_type = self.request.validated["doc_type"]
#         i = self.request.validated["i"]

#         cache_key = _get_cache_key(doc_type, i)
#         etag_cache(self.request, cache_key)

#         return get_or_create(cache_sitemap, cache_key, functools.partial(_get_sitemap, doc_type, i))


# def _get_cache_key(doc_type=None, i=None):
#     if doc_type:
#         return "{}-{}-{}-{}".format(doc_type, i, date.today().isoformat(), caching.CACHE_VERSION)
#     else:
#         return "{}-{}".format(date.today().isoformat(), caching.CACHE_VERSION)


# def _get_sitemap(doc_type, i):
#     fields = [Document.document_id, DocumentLocale.lang, DocumentLocale.title, CacheVersion.last_updated]

#     # include `title_prefix` for routes
#     is_route = doc_type == ROUTE_TYPE
#     if is_route:
#         fields.append(RouteLocale.title_prefix)

#     base_query = (
#         DBSession.query(*fields)
#         .select_from(Document)
#         .join(DocumentLocale, Document.document_id == DocumentLocale.document_id)
#     )

#     if is_route:
#         # joining on `RouteLocale.__table_` instead of `RouteLocale` to
#         # avoid that SQLAlchemy create an additional join on DocumentLocale
#         base_query = base_query.join(RouteLocale.__table__, DocumentLocale.id == RouteLocale.id)

#     base_query = (
#         base_query.join(CacheVersion, Document.document_id == CacheVersion.document_id)
#         .filter(Document.redirects_to.is_(None))
#         .filter(Document.type == doc_type)
#         .order_by(Document.document_id, DocumentLocale.lang)
#         .limit(PAGES_PER_SITEMAP)
#         .offset(PAGES_PER_SITEMAP * i)
#     )

#     document_locales = base_query.all()

#     if not document_locales:
#         raise HTTPNotFound()

#     return {"pages": [_format_page(locale, is_route) for locale in document_locales]}


# def _format_page(document_locale, is_route):
#     if not is_route:
#         doc_id, lang, title, last_updated = document_locale
#     else:
#         doc_id, lang, title, last_updated, title_prefix = document_locale

#     page = {"document_id": doc_id, "lang": lang, "title": title, "lastmod": last_updated.isoformat()}

#     if is_route:
#         page["title_prefix"] = title_prefix

#     return page
