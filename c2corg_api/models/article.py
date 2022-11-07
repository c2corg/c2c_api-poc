from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden


class Article:
    fixed_attributes = ["anonymous"]

    @classmethod
    def on_creation(cls, version):
        version.data |= {"author": {"user_id": current_user.id}}

    @classmethod
    def on_new_version(cls, old_version, new_version):
        # only moderator can change author
        if old_version.data["author"]["user_id"] != new_version.data["author"]["user_id"]:
            if not current_user.is_moderator:
                raise Forbidden("You are not allowed to change author")

        # check changes on article licence
        articles_types = (old_version.data["article_type"], new_version.data["article_type"])
        if articles_types == ("collab", "personal"):  # from collab to personal
            if not current_user.is_moderator:
                raise BadRequest("Article type cannot be changed for collaborative articles")
        elif articles_types == ("personal", "collab"):  # from personal to collab
            if new_version.data["author"]["user_id"] != current_user.id:
                raise Forbidden("You are not allowed to change article type")

        # only current author, or moderator can change personnal article
        if new_version.data["article_type"] == "personal":
            if new_version.data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
                raise Forbidden("You are not allowed to edit this article")
