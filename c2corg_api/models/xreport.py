from flask import current_app
from flask_camp.models import DocumentVersion
from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden


class Xreport:
    @classmethod
    def on_creation(cls, version: DocumentVersion):
        if version.data["anonymous"]:
            anonymous_user_id = current_app.config["ANONYMOUS_USER_ID"]
            version.data |= {"author": {"user_id": anonymous_user_id}}
            version.user_id = anonymous_user_id
        else:
            version.data |= {"author": {"user_id": current_user.id}}

    @classmethod
    def on_new_version(cls, old_version: DocumentVersion, new_version: DocumentVersion):
        # only moderator can change author
        if old_version.data["author"]["user_id"] != new_version.data["author"]["user_id"]:
            if not current_user.is_moderator:
                raise Forbidden("You are not allowed to change author")

        if (
            old_version.data["author"]["user_id"] != current_user.id
            and not current_user.is_moderator
            and current_user.id not in old_version.data["associations"]
        ):
            raise Forbidden("You are not allowed to edit this document")

        for attribute in ["anonymous"]:
            if old_version.data[attribute] != new_version.data[attribute]:
                raise BadRequest(f"You cannot modify {attribute}")
