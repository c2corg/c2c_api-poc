from flask import request
from sqlalchemy import and_

from c2corg_api.search import DocumentSearch


def update_search_query(query):
    locale_lang = request.args.get("l", default=None, type=str)
    document_type = request.args.get("document_type", default=None, type=str)

    criterions = []

    if locale_lang is not None:
        criterions.append(DocumentSearch.available_langs.contains([locale_lang]))

    if document_type is not None:
        criterions.append(DocumentSearch.document_type == document_type)

    if len(criterions) != 0:
        query = query.join(DocumentSearch).where(and_(*criterions))

    return query
