from flask import request
from flask_camp import allow, current_api
from sqlalchemy import select
from werkzeug.exceptions import BadRequest

from c2corg_api.models import models
from c2corg_api.search import DocumentLocaleSearch, DocumentSearch, slugify

rule = "/search"


@allow("anonymous", "authenticated")
def get():
    q = request.args.get("q")

    if q is None:
        raise BadRequest("q parameter is not defined")

    query = (
        select(DocumentLocaleSearch.id, DocumentSearch.document_type)
        .join(DocumentSearch, DocumentSearch.id == DocumentLocaleSearch.id)
        .filter(DocumentLocaleSearch.slugified_title.like("%{}%".format(slugify(q))))
    )

    result = {document_type: set() for document_type in models}

    for document_id, document_type in current_api.database.session.execute(query):
        result[document_type].add(document_id)

    result = {
        document_type: [current_api.get_cooked_document(document_id) for document_id in result[document_type]]
        for document_type in result
    }

    return result
