from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden


class Xreport:
    fixed_attributes = ["anonymous"]

    @classmethod
    def on_creation(cls, version):
        version.data |= {"author": {"user_id": current_user.id}}

    @classmethod
    def on_new_version(cls, old_version, new_version):

        if new_version.data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
            raise Forbidden("You are not allowed to edit this document")

        for attribute in cls.fixed_attributes:
            if old_version.data[attribute] != new_version.data[attribute]:
                raise BadRequest(f"You cannot modify {attribute}")
