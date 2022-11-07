from flask_camp import current_api
from flask_camp.models import Document

USERPROFILE_TYPE = "profile"


class UserProfile:

    @staticmethod
    def create(user, locale_langs, session=None):
        from c2corg_api.search import DocumentSearch

        # TODO on legacy removal, removes session parameter
        session = current_api.database.session if session is None else session
        assert user.id is not None, "Dev check..."

        data = UserProfile.get_default_data(user, categories=[], locale_langs=locale_langs)
        user_page = Document.create(comment="Creation of user page", data=data, author=user)

        session.flush()
        search_item = DocumentSearch(id=user_page.id)
        session.add(search_item)

        search_item.update(user_page.last_version, user=user)

    @staticmethod
    def get_default_data(user, categories, locale_langs):
        locales = {lang: {"description": None, "summary": None, "lang": lang} for lang in locale_langs}

        return {
            "type": USERPROFILE_TYPE,
            "user_id": user.id,
            "locales": locales,
            "categories": categories,
            "areas": [],  # TODO: remove this
            "name": user.data["full_name"],
            "geometry": {"geom": '{"type":"point", "coordinates":null}'},  # TODO : not json,
            "associations": [],
        }
