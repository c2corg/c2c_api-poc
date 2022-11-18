from flask import request
from flask_login import current_user
from flask_camp import allow, current_api
from flask_camp.views.content import tags as tags_view
from flask_camp.models import Tag
from sqlalchemy import and_


def get_tag_relation(user_id, document_id):
    return (
        current_api.database.session.query(Tag)
        .filter(and_(Tag.user_id == user_id, Tag.document_id == document_id, Tag.name == "todo"))
        .first()
    )


class DocumentTagAdd:
    rule = "/tags/add"

    @allow("authenticated")
    def post(self):
        data = request.get_json()

        data = {
            "document_id": data["document_id"],
            "name": "todo",
        }

        request._cached_json = (data, data)

        return tags_view.post()


class DocumentTagRemove:
    rule = "/tags/remove"

    @allow("authenticated")
    def post(self):
        data = request.get_json()

        data = {
            "document_id": data["document_id"],
            "name": "todo",
        }

        request._cached_json = (data, data)

        return tags_view.delete()


class DocumentTagHas:
    rule = "/tags/has/<int:document_id>"

    @allow("authenticated")
    def get(self, document_id):
        tag = get_tag_relation(user_id=current_user.id, document_id=document_id)

        return {"todo": tag is not None}
