from flask import request
from sqlalchemy import and_
from werkzeug.exceptions import BadRequest

from c2corg_api.models import XREPORT_TYPE, USERPROFILE_TYPE
from c2corg_api.search import DocumentSearch


def update_search_query(query):
    document_type = request.args.get("document_type", default=None, type=str)

    locale_lang = request.args.get("l", default=None, type=str)
    activities = request.args.get("act", default=None, type=str)
    area_types = request.args.get("atyp", default=None, type=str)

    criterions = []

    if document_type is not None:
        criterions.append(DocumentSearch.document_type == document_type)

        if document_type == USERPROFILE_TYPE:
            criterions.append(DocumentSearch.user_is_validated == True)

    if locale_lang is not None:
        criterions.append(DocumentSearch.available_langs.contains([locale_lang]))

    if activities is not None:
        if document_type is None:
            raise BadRequest("Please set a document type to filter activities")

        if document_type == XREPORT_TYPE:
            criterions.append(DocumentSearch.event_activity.in_(activities.split(",")))
        else:
            criterions.append(DocumentSearch.activities.contains(activities.split(",")))

    if area_types is not None:
        criterions.append(DocumentSearch.area_type.in_(area_types.split(",")))

    if len(criterions) != 0:
        query = query.join(DocumentSearch).where(and_(*criterions))

    return query
