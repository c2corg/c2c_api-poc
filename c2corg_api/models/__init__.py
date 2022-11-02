from flask_camp import current_api
from flask_camp.models import Document, BaseModel, User
from sqlalchemy import Column, ForeignKey, Integer, delete, select
from sqlalchemy.orm import relationship

USERPROFILE_TYPE = "profile"
AREA_TYPE = "area"
ARTICLE_TYPE = "article"
WAYPOINT_TYPE = "waypoint"

VALIDATION_EXPIRE_DAYS = 3

# Make the link between the user and the profile page in DB
class ProfilePageLink(BaseModel):
    id = Column(Integer, primary_key=True)

    document_id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    document = relationship(Document, cascade="all,delete")

    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    user = relationship(User, cascade="all,delete")


def get_default_user_profile_data(user, categories, locale_langs):
    locales = {lang: {"topic_id": None, "description": None, "summary": None, "lang": lang} for lang in locale_langs}

    return {
        "type": USERPROFILE_TYPE,
        "user_id": user.id,
        "locales": locales,
        "categories": categories,
        "areas": [],
        "name": user.data["full_name"],
        "geometry": {"geom": '{"type":"point", "coordinates":null}'},  # TODO : not json
    }


def create_user_profile(user, locale_langs, session=None):
    # TODO on legacy removal, removes session parameter
    session = current_api.database.session if session is None else session
    assert user.id is not None, "Dev check..."

    data = get_default_user_profile_data(user, categories=[], locale_langs=locale_langs)
    user_page = Document.create(comment="Creation of user page", data=data, author=user)
    session.add(ProfilePageLink(document=user_page, user=user))
