from flask import request
from flask_camp import allow, current_api
from flask_camp.views.account import current_user as current_user_view

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
