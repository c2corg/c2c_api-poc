from flask import request

from c2corg_api.search import DocumentSearch


def update_search_query(query):
    locale_lang = request.args.get("l", default=None, type=str)

    if locale_lang is not None:
        query = query.join(DocumentSearch).where(DocumentSearch.available_langs.contains([locale_lang]))

    return query
