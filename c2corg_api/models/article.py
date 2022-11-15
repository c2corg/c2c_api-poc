from flask_camp.models import Document, DocumentVersion
from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden

from c2corg_api.models._document import BaseModelHooks


class Article(BaseModelHooks):
    fixed_attributes = ["anonymous"]

    def before_create_document(self, version):
        super().before_create_document(version)
        version.data |= {"author": {"user_id": current_user.id}}

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        super().before_update_document(document, old_version, new_version)
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

    def update_document_search_table(self, document: Document, version: DocumentVersion, user=None, session=None):
        search_item = super().update_document_search_table(document, user, session)
        search_item.activities = version.data["activities"]
