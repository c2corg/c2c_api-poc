from datetime import datetime, timezone
import json
import logging
from math import ceil
from slugify import slugify

from flask import Response, request
from flask_camp import current_api, allow
from sqlalchemy.sql.functions import func
from werkzeug.exceptions import BadRequest

from c2corg_api.search import DocumentSearch, DocumentLocaleSearch
from c2corg_api.models import USERPROFILE_TYPE, ROUTE_TYPE, models as document_types


log = logging.getLogger(__name__)

# Search engines accept not more than 50000 urls per sitemap,
# and the sitemap files may not exceed 10 MB. With 50000 urls the sitemaps
# are not bigger than 9MB, but to be safe we are using 45000 urls per sitemap.
# see http://www.sitemaps.org/protocol.html
PAGES_PER_SITEMAP = 45000


class _Sitemaps:
    @staticmethod
    def get_locales_per_type():
        return (
            current_api.database.session.query(DocumentSearch.document_type, func.count().label("count"))
            .join(DocumentLocaleSearch, DocumentSearch.id == DocumentLocaleSearch.id)
            .filter(DocumentSearch.document_type != USERPROFILE_TYPE)
            .group_by(DocumentSearch.document_type)
            .all()
        )


class _Sitemap:
    @staticmethod
    def get_locales(document_type, page):
        fields = [
            DocumentSearch.id,
            DocumentLocaleSearch.lang,
            DocumentLocaleSearch.title_prefix,
            DocumentLocaleSearch.title,
            DocumentSearch.timestamp,
        ]

        query = (
            current_api.database.session.query(*fields)
            .select_from(DocumentLocaleSearch)
            .join(DocumentSearch, DocumentSearch.id == DocumentLocaleSearch.id)
            .filter(DocumentSearch.document_type == document_type)
            .order_by(DocumentLocaleSearch.id, DocumentLocaleSearch.lang)
            .limit(PAGES_PER_SITEMAP)
            .offset(PAGES_PER_SITEMAP * page)
        )

        return query.all()


class SitemapsRest(_Sitemaps):
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

        document_locales_per_type = self.get_locales_per_type()

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


class SitemapRest(_Sitemap):
    rule = "/sitemaps/<string:document_type>/<int:page>"

    @allow("anonymous")
    def get(self, document_type, page):
        """Returns the information needed to generate a sitemap for a given type and sitemap page number."""

        if document_type not in document_types:
            raise BadRequest("Invalid document type")

        document_locales = self.get_locales(document_type, page)

        # include `title_prefix` for routes
        is_route = document_type == ROUTE_TYPE
        data = {"pages": [self.format_page(is_route, *locale) for locale in document_locales]}

        result = Response(response=json.dumps(data), content_type="application/json")
        result.add_etag()  # TODO : compute it only one time per day
        result.make_conditional(request)

        return result

    @staticmethod
    def format_page(is_route, doc_id, lang, title, title_prefix, last_updated):
        page = {"document_id": doc_id, "lang": lang, "title": title, "lastmod": last_updated.isoformat()}

        if is_route:
            page["title_prefix"] = title_prefix

        return page


class SitemapsXml(_Sitemaps):
    rule = "/sitemaps.xml"

    @allow("anonymous")
    def get(self):
        """Returns a sitemap index file.
        See: http://www.sitemaps.org/protocol.html

        The response consists of a list of URLs of sitemaps.

        <?xml version="1.0" encoding="UTF-8"?>
            <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <sitemap>
                    <loc>https://api.camptocamp.org/sitemaps.xml/w/0.xml</loc>
                    <lastmod>2019-02-11T18:01:49.193770+00:00</lastmod>
                </sitemap>
                <sitemap>
                    <loc>https://api.camptocamp.org/sitemaps.xml/a/0.xml</loc>
                    <lastmod>2019-02-11T18:01:49.193770+00:00</lastmod>
                </sitemap>
                <sitemap>
                    <loc>https://api.camptocamp.org/sitemaps.xml/i/0.xml</loc>
                    <lastmod>2019-02-11T18:01:49.193770+00:00</lastmod>
                </sitemap>
                <sitemap>
                    <loc>https://api.camptocamp.org/sitemaps.xml/i/1.xml</loc>
                    <lastmod>2019-02-11T18:01:49.193770+00:00</lastmod>
                </sitemap>
            </sitemap>
        """

        document_locales_per_type = self.get_locales_per_type()

        sitemaps = []

        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        lastmod = now.isoformat()

        template = """<sitemap>
        <loc>https://api.camptocamp.org/sitemaps.xml/{doc_type}/{i}.xml</loc>
        <lastmod>{lastmod}</lastmod>
        </sitemap>"""

        for doc_type, count in document_locales_per_type:
            num_sitemaps = ceil(count / PAGES_PER_SITEMAP)
            sitemaps_for_type = [
                template.format(doc_type=doc_type, i=i, lastmod=lastmod) for i in range(0, num_sitemaps)
            ]
            sitemaps.extend(sitemaps_for_type)

        body = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {}
        </sitemapindex>""".format(
            "\n".join(sitemaps)
        )

        result = Response(response=body, content_type="text/xml")
        result.add_etag()  # TODO : compute it only one time per day
        result.make_conditional(request)

        return result


class SitemapXml(_Sitemap):
    rule = "/sitemaps.xml/<string:document_type>/<int:page>.xml"

    @allow("anonymous")
    def get(self, document_type, page):
        """Returns a sitemap file for a given type and sitemap page number."""

        if document_type not in document_types:
            raise BadRequest("Invalid document type")

        document_locales = self.get_locales(document_type, page)

        body = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {}
        </urlset>""".format(
            "\n".join([self.format_page(document_type, *locale) for locale in document_locales])
        )

        result = Response(response=body, content_type="text/xml")
        result.add_etag()  # TODO : compute it only one time per day
        result.make_conditional(request)

        return result

    @staticmethod
    def format_page(document_type, doc_id, lang, title_prefix, title, last_updated):

        page = {
            "document_id": doc_id,
            "lang": lang,
            "lastmod": last_updated.isoformat(),
            "document_type": document_type,
        }

        if title_prefix:
            page["title"] = slugify(f"{title_prefix} {title}")
        else:
            page["title"] = slugify(title)

        return """<url>
    <loc>https://www.camptocamp.org/{document_type}/{document_id}/{lang}/{title}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    </url>""".format(
            **page
        )
