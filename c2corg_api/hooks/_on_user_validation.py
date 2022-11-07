from flask import current_app

from c2corg_api.hooks._tools import get_profile_document
from c2corg_api.search import update_document_search_table
from c2corg_api.security.discourse_client import get_discourse_client


def on_user_validation(user, sync_sso=True):

    profile_document = get_profile_document(user)

    update_document_search_table(profile_document, user=user)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)
