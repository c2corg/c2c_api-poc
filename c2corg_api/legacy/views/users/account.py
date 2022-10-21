from copy import deepcopy
from flask import request
from flask_login import current_user
from flask_camp import allow
from flask_camp.views.account import current_user as current_user_view
from flask_camp.views.account import user as user_view

rule = "/users/account"


@allow("authenticated", allow_blocked=True)
def get():
    result = current_user_view.get()
    user = result["user"]

    # v6 username : login field, dropped
    # v6 name : label, as now, saved in ui preference
    # v6 forum_username : now used as unique identifier

    user["forum_username"] = user["name"]
    user["username"] = user["name"]
    user["name"] = user["ui_preferences"]["full_name"]

    user["is_profile_public"] = user["ui_preferences"]["is_profile_public"]

    return user


@allow("authenticated", allow_blocked=True)
def post():
    body = request.get_json()

    new_body = {
        "password": body["currentpassword"],
        "ui_preferences": deepcopy(current_user.ui_preferences),
    }

    if "forum_username" in body:
        new_body["name"] = body["forum_username"].strip().lower()

    if "email" in body:
        new_body["email"] = body["email"]

    if "name" in body:
        new_body["ui_preferences"]["full_name"] = body["name"]

    if "is_profile_public" in body:
        new_body["ui_preferences"]["is_profile_public"] = body["is_profile_public"]

    request._cached_json = (new_body, new_body)

    user_view.post(int(current_user.id))

    return {"status": "ok"}
