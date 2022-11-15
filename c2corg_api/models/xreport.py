from flask import current_app
from flask_camp.models import Document, DocumentVersion
from flask_camp._utils import JsonResponse
from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden

from c2corg_api.models._document import BaseModelHooks


class Xreport(BaseModelHooks):

    private_fields = ("author_status", "activity_rate", "age", "gender", "previous_injuries", "autonomy")

    def after_get_document(self, response: JsonResponse):
        super().before_create_document(response)
        document_data = response.data["document"]["data"]

        response.headers["Cache-Control"] = "private"

        if document_data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
            for field in self.private_fields:
                document_data[field] = None  # overwrite it with None

    def before_create_document(self, version: DocumentVersion):
        super().before_create_document(version)

        if version.data["anonymous"]:
            anonymous_user_id = current_app.config["ANONYMOUS_USER_ID"]
            version.data |= {"author": {"user_id": anonymous_user_id}}
            version.user_id = anonymous_user_id
        else:
            version.data |= {"author": {"user_id": current_user.id}}

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        super().before_update_document(document, old_version, new_version)
        # only moderator can change author
        if old_version.data["author"]["user_id"] != new_version.data["author"]["user_id"]:
            if not current_user.is_moderator:
                raise Forbidden("You are not allowed to change author")

        if (
            old_version.data["author"]["user_id"] != current_user.id
            and not current_user.is_moderator
            and current_user.id not in old_version.data["associations"].get("profile", [])
        ):
            raise Forbidden("You are not allowed to edit this document")

        for attribute in ["anonymous"]:
            if old_version.data[attribute] != new_version.data[attribute]:
                raise BadRequest(f"You cannot modify {attribute}")

    def update_document_search_table(self, document: Document, version: DocumentVersion, user=None, session=None):
        search_item = super().update_document_search_table(document, user, session)
        search_item.event_activity = version.data["event_activity"]
