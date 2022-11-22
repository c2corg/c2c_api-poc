from flask import request, current_app
from flask_camp import current_api
from flask_camp.models import Document, DocumentVersion, User
from flask_camp.utils import JsonResponse
from sqlalchemy import delete
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.exceptions import BadRequest, NotFound

from c2corg_api.hooks._tools import check_user_name, get_profile_document
from c2corg_api.models import models
from c2corg_api.models.userprofile import UserProfile
from c2corg_api.schemas import schema_validator
from c2corg_api.search import DocumentSearch, DocumentLocaleSearch
from c2corg_api.security.discourse_client import get_discourse_client

from ._before_block_user import before_block_user
from ._update_search_query import update_search_query


def _get_model(version):
    document_type = version.data["type"]

    try:
        return models[document_type]
    except KeyError as e:
        raise BadRequest(f"Unknow document type: {document_type}") from e


def after_get_document(response: JsonResponse):
    models[response.data["document"]["data"]["type"]].after_get_document(response)


def before_create_document(document):
    _get_model(document.last_version).before_create_document(document=document, version=document.last_version)


def before_update_document(document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
    _get_model(old_version).before_update_document(document, old_version=old_version, new_version=new_version)


def before_merge_documents(source_document, target_document):
    def get_type(document):
        return document.last_version.data["type"]

    if get_type(source_document) != get_type(target_document):
        raise BadRequest()

    delete(DocumentSearch).where(DocumentSearch.id == source_document.id)
    delete(DocumentLocaleSearch).where(DocumentLocaleSearch.id == source_document.id)


def before_create_user(user):
    check_user_name(user.name)
    schema_validator.validate(user.data, "user_data.json")
    UserProfile().create(user, ["fr"])


def before_update_user(user: User, sync_sso=True):

    data = request.get_json()

    if "name" in data:
        check_user_name(user.name)

    follow = list(set(user.data["feed"]["follow"]))
    user.data["feed"]["follow"] = follow  # remove duplicates
    flag_modified(user, "data")

    schema_validator.validate(user.data, "user_data.json")

    if len(follow) != 0:
        real_user_ids = [r[0] for r in current_api.database.session.query(User.id).filter(User.id.in_(follow)).all()]
        if len(follow) != len(real_user_ids):
            raise NotFound(f"{follow} {real_user_ids}")

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


def before_validate_user(user, sync_sso=True):

    profile_document = get_profile_document(user)
    search_item, _ = UserProfile().get_search_items(profile_document, langs=[])
    search_item.user_is_validated = True
    UserProfile().update_document_search_table(document=profile_document, version=profile_document.last_version)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)
