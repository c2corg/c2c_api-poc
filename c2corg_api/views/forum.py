from flask import request, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

from flask_camp import allow
from flask_camp.models import Document

from c2corg_api.models._core import ui_url_types
from c2corg_api.schemas import schema
from c2corg_api.security.discourse_client import get_discourse_client

rule = "/forum/topics"


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

    if locale.get("topic_id") is not None:
        raise BadRequest("Topic already exists")

    document_type = ui_url_types[data["type"]]

    document_path = f"/{document_type}/{document_id}/{lang}"
    title = locale.get("title", document_path) or document_path
    content = '<a href="https://www.camptocamp.org{document_path}">{title}</a>'

    category = current_app.config["C2C_DISCOURSE_COMMENT_CATEGORY"]

    client = get_discourse_client(current_app.config)

    try:
        title = f"{document_id}_{lang}"
        response = client.client.create_post(content, title=title, category=category)
    except Exception as e:
        current_app.logger.error("Error with Discourse: {}".format(str(e)), exc_info=True)
        raise InternalServerError("Error with Discourse") from e

    # if "topic_id" in response:
    #     topic_id = response['topic_id']

    #     locale["topic_id"] = document_topic
    #     update_cache_version_direct(locale.document_id)
    #     DBSession.flush()

    #     if locale.type == document_types.OUTING_TYPE:
    #         try:
    #             self.invite_participants(client, locale, topic_id)
    #         except Exception:
    #             log.error('Inviting participants of outing {} failed'
    #                         .format(locale.document_id),
    #                         exc_info=True)

    # return response

    return {}
