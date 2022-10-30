from flask import request
from flask_camp import allow
from flask_camp.views.account import current_user as current_user_view
from flask_camp.views.account import user as user_view
from flask_login import current_user
from werkzeug.exceptions import BadRequest

from c2corg_api.legacy.converter import get_legacy_doc


rule = "/users/preferences"


@allow("authenticated", allow_blocked=True)
def get():
    lang = request.args.get("pl", None)
    result = current_user_view.get()["user"]["data"]["feed"]

    result["areas"] = [get_legacy_doc(area_id) for area_id in result["areas"]]

    if lang is not None:
        for area in result["areas"]:
            area["locales"] = [locale for locale in area["locales"] if locale["lang"] == lang]

    return result


@allow("authenticated", allow_blocked=True)
def post():
    # convert v6 request to flask_camp request
    data = current_user.data
    data["feed"] = request.get_json()

    try:
        data["feed"]["areas"] = [area["document_id"] for area in data["feed"]["areas"]]
    except KeyError as e:
        raise BadRequest() from e

    body = {"user": {"data": data}}

    request._cached_json = (body, body)

    return user_view.put(current_user.id)
