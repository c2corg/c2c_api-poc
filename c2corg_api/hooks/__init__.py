from flask import current_app
from flask_camp.models import Document, DocumentVersion
from flask_camp.utils import JsonResponse
from werkzeug.exceptions import BadRequest

from c2corg_api.hooks._tools import check_user_name, get_profile_document
from c2corg_api.models import models
from c2corg_api.models.userprofile import UserProfile
from c2corg_api.security.discourse_client import get_discourse_client

from ._before_block_user import before_block_user
from ._before_update_user import before_update_user
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
    _get_model(document.last_version).before_create_document(version=document.last_version)


def before_update_document(document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
    _get_model(old_version).before_update_document(document, old_version=old_version, new_version=new_version)


def before_merge_documents(a, b):
    _get_model(a.last_version).before_merge_documents(a, b)


def before_create_user(user):
    check_user_name(user.name)
    UserProfile().create(user, ["fr"])


def before_validate_user(user, sync_sso=True):

    profile_document = get_profile_document(user)
    search_item = UserProfile().get_search_item(profile_document)
    search_item.user_is_validated = True
    UserProfile().update_document_search_table(document=profile_document, version=profile_document.last_version)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)
