from copy import deepcopy
from flask import request
from flask_login import current_user
from flask_camp import allow, current_api
from flask_camp.views.account import current_user as current_user_view

rule = "/users/preferences"


@allow("authenticated", allow_blocked=True)
def get():
    result = current_user_view.get()["user"]["ui_preferences"]["feed"]

    result["areas"] = [current_api.get_cooked_document(area_id)["legacy"] for area_id in result["areas"]]

    return result
