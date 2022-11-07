import re
from flask_camp import current_api
from flask_camp.models import Document
from sqlalchemy import select
from werkzeug.exceptions import BadRequest

from c2corg_api.search import DocumentSearch


# https://github.com/discourse/discourse/blob/master/app/models/username_validator.rb
def check_user_name(value):
    if len(value) < 3:
        raise BadRequest("Shorter than minimum length 3")
    if len(value) > 25:
        raise BadRequest("Longer than maximum length 25")
    if re.search(r"[^\w.-]", value):
        raise BadRequest("Contain invalid character(s)")
    if re.match(r"\W", value[0]):
        raise BadRequest("First character is invalid")
    if re.match(r"[^A-Za-z0-9]", value[-1]):
        raise BadRequest("Last character is invalid")
    if re.search(r"[-_\.]{2,}", value):
        raise BadRequest("Contains consecutive special characters")
    if re.search((r"\.(js|json|css|htm|html|xml|jpg|jpeg|png|gif|bmp|ico|tif|tiff|woff)$"), value):
        raise BadRequest("Ended by confusing suffix")


def get_profile_document(user):
    query = select(DocumentSearch.id).where(DocumentSearch.user_id == user.id)
    result = current_api.database.session.execute(query)
    document_id = list(result)[0][0]

    return Document.get(id=document_id)

