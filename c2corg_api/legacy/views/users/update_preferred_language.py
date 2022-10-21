from copy import deepcopy
from flask import request
from flask_login import current_user
from flask_camp import allow
from flask_camp.views.account import user as user_view

rule = "/users/update_preferred_language"


@allow("authenticated", allow_blocked=True)
def post():
    body = request.get_json()

    new_body = {
        "ui_preferences": deepcopy(current_user.ui_preferences),
    }

    new_body["ui_preferences"]["lang"] = body["lang"]

    request._cached_json = (new_body, new_body)

    user_view.post(int(current_user.id))

    return {"status": "ok"}
