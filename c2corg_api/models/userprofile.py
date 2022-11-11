from flask_camp import current_api
from flask_camp.models import Document
from flask_camp._utils import JsonResponse
from flask_login import current_user
from sqlalchemy import select
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from c2corg_api.search import DocumentSearch
from c2corg_api.models._core import BaseModelHooks, USERPROFILE_TYPE


class UserProfile(BaseModelHooks):
    @staticmethod
    def create(user, locale_langs, geom=None, session=None):
        # TODO on legacy removal, removes session parameter
        session = current_api.database.session if session is None else session
        assert user.id is not None, "Dev check..."

        data = UserProfile.get_default_data(user, categories=[], locale_langs=locale_langs, geom=geom)
        user_page = Document.create(comment="Creation of user page", data=data, author=user)

        session.flush()
        search_item = DocumentSearch(id=user_page.id)
        session.add(search_item)

        search_item.update(user_page, user=user)

    @staticmethod
    def get_default_data(user, categories, locale_langs, geom=None):
        locales = {lang: {"lang": lang} for lang in locale_langs}

        result = {
            "type": USERPROFILE_TYPE,
            "user_id": user.id,
            "locales": locales,
            "categories": categories,
            "associations": {},
            "name": user.data["full_name"],
        }

        if geom is not None:
            result["geometry"] = {"geom": geom}

        return result

    def after_get_document(self, response: JsonResponse):
        query = select(DocumentSearch.user_is_validated).where(DocumentSearch.id == response.data["document"]["id"])
        result = current_api.database.session.execute(query)
        user_is_validated = list(result)[0][0]

        if not user_is_validated:
            raise NotFound()

    def on_creation(self, version):
        raise BadRequest("Profile page can't be created without an user")

    def on_new_version(self, old_version, new_version):
        user_id = self.get_user_id_from_profile_id(old_version.document_id)
        if user_id != current_user.id:
            if not current_user.is_moderator:
                raise Forbidden()

    def get_user_id_from_profile_id(self, profile_id):
        query = select(DocumentSearch.user_id).where(DocumentSearch.id == profile_id)
        result = current_api.database.session.execute(query)
        user_id = list(result)[0][0]

        return user_id
