from flask import request
from flask_camp import allow, current_api
from flask_camp.views.account import current_user as current_user_view
from flask_camp.views.account import user as user_view
from flask_login import current_user
from werkzeug.exceptions import BadRequest

rule = "/users/preferences"


@allow("authenticated", allow_blocked=True)
def get():
    lang = request.args.get("pl", None)
    result = current_user_view.get()["user"]["ui_preferences"]["feed"]

    result["areas"] = [current_api.get_cooked_document(area_id)["legacy"] for area_id in result["areas"]]

    if lang is not None:
        for area in result["areas"]:
            area["locales"] = [locale for locale in area["locales"] if locale["lang"] == lang]

    return result


@allow("authenticated", allow_blocked=True)
def post():
    # convert v6 request to flask_camp request
    ui_preferences = current_user.ui_preferences
    ui_preferences["feed"] = request.get_json()
    body = {"ui_preferences": ui_preferences}

    try:
        body["ui_preferences"]["feed"]["areas"] = [
            area["document_id"] for area in body["ui_preferences"]["feed"]["areas"]
        ]
    except KeyError as e:
        raise BadRequest() from e

    request._cached_json = (body, body)

    return user_view.post(current_user.id)
