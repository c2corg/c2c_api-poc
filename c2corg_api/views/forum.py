from flask import request, current_app
from flask_camp import allow, current_api
from flask_camp.models import Document, User
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.exceptions import BadRequest, InternalServerError

from c2corg_api.models._core import ui_url_types, OUTING_TYPE
from c2corg_api.schemas import schema
from c2corg_api.search import DocumentSearch
from c2corg_api.security.discourse_client import get_discourse_client

rule = "/forum/topics"


def _invite_participants(client, profile_ids, topic_id):
    participants = (
        current_api.database.session.query(User.name)
        .join(DocumentSearch, DocumentSearch.user_id == User.id)
        .filter(DocumentSearch.id.in_(profile_ids))
        .group_by(User.name)
    )

    for (name,) in participants:
        try:
            client.client.invite_user_to_topic_by_username(name, topic_id)
        except Exception:
            current_app.logger.exception(f"Inviting forum user {name} in topic {topic_id} failed")


@schema("requests/post_topics.json")
@allow("authenticated")
def post():
    body = request.get_json()
    document_id, lang = body["document_id"], body["lang"]

    document = Document.get(id=document_id, with_for_update=True)
    data = document.last_version.data
    locale = data["locales"].get(lang)

    if locale is None:
        raise BadRequest("Document not found")

    if document.data["topics"].get(lang) is not None:
        raise BadRequest("Topic already exists")

    document_type = ui_url_types[data["type"]]

    document_path = f"/{document_type}/{document_id}/{lang}"
    title = locale.get("title", document_path) or document_path
    content = f'<a href="https://www.camptocamp.org{document_path}">{title}</a>'

    category = current_app.config["C2C_DISCOURSE_COMMENT_CATEGORY"]

    client = get_discourse_client(current_app.config)

    try:
        title = f"{document_id}_{lang}"
        response = client.client.create_post(content, title=title, category=category)
    except Exception as e:
        current_app.logger.exception("Error with Discourse: {e}")
        raise InternalServerError("Error with Discourse") from e

    if "topic_id" in response:
        topic_id = response["topic_id"]
        document.data["topics"][lang] = topic_id
        flag_modified(document, "data")
        document.clear_memory_cache()

        current_api.database.session.commit()

        if document.last_version.data["type"] == OUTING_TYPE:
            try:
                _invite_participants(client, document.last_version.data["associations"]["profile"], topic_id)
            except Exception:
                current_app.logger.exception(f"Inviting participants of outing {document_id} failed")

    return {"status": "ok"}
