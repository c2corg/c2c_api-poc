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
from c2corg_api.search import DocumentSearch, DocumentLocaleSearch
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
            current_api.database.session.query(DocumentSearch.document_type, func.count().label("count"))
            .join(DocumentLocaleSearch, DocumentSearch.id == DocumentLocaleSearch.id)
            .filter(DocumentSearch.document_type != USERPROFILE_TYPE)
            .group_by(DocumentSearch.document_type)
            .all()
        )

        sitemaps = []
        for doc_type, doc_count in document_locales_per_type:
            num_sitemaps = ceil(doc_count / PAGES_PER_SITEMAP)
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
        """Returns the information needed to generate a sitemap for a given type and sitemap page number."""

        if document_type not in document_types:
            raise BadRequest("Invalid document type")

        fields = [DocumentSearch.id, DocumentLocaleSearch.lang, DocumentLocaleSearch.title, DocumentSearch.last_updated]

        #     # include `title_prefix` for routes
        is_route = document_type == ROUTE_TYPE
        #     if is_route:
        #         fields.append(RouteLocale.title_prefix)

        document_locales = (
            current_api.database.session.query(*fields)
            .select_from(DocumentLocaleSearch)
            .join(DocumentSearch, DocumentSearch.id == DocumentLocaleSearch.id)
            .filter(DocumentSearch.document_type == document_type)
            .order_by(DocumentLocaleSearch.id, DocumentLocaleSearch.lang)
            .limit(PAGES_PER_SITEMAP)
            .offset(PAGES_PER_SITEMAP * page)
            .all()
        )

        data = {"pages": [_format_page(locale, is_route) for locale in document_locales]}

        result = Response(response=json.dumps(data), content_type="application/json")
        result.add_etag()  # TODO : compute it only one time per day
        result.make_conditional(request)

        return result


# def _get_cache_key(doc_type=None, i=None):
#     if doc_type:
#         return "{}-{}-{}-{}".format(doc_type, i, date.today().isoformat(), caching.CACHE_VERSION)
#     else:
#         return "{}-{}".format(date.today().isoformat(), caching.CACHE_VERSION)


def _format_page(document_locale, is_route):
    if not is_route:
        doc_id, lang, title, last_updated = document_locale
    else:
        doc_id, lang, title, last_updated, title_prefix = document_locale

    page = {"document_id": doc_id, "lang": lang, "title": title, "lastmod": last_updated.isoformat()}

    if is_route:
        page["title_prefix"] = title_prefix

    return page
