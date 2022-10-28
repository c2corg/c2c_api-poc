from copy import deepcopy
from flask import request
from flask_login import current_user
from flask_camp import allow, current_api
from flask_camp.models import User
from flask_camp.views.account import current_user as current_user_view
from flask_camp.views.account import user as user_view
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest

from c2corg_api.hooks import check_user_name

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
    user["name"] = user["data"]["full_name"]

    user["is_profile_public"] = user["data"]["is_profile_public"]

    return user


@allow("authenticated", allow_blocked=True)
def post():
    body = request.get_json()

    user = {
        "password": body["currentpassword"],
        "data": deepcopy(current_user.data),
    }

    if "forum_username" in body:
        user["name"] = body["forum_username"].strip().lower()
        check_user_name(user["name"])

    if "email" in body:
        user["email"] = body["email"]

    if "name" in body:
        user["data"]["full_name"] = body["name"]

    if "is_profile_public" in body:
        user["data"]["is_profile_public"] = body["is_profile_public"]

    new_body = {"user": user, "comment": "default comment"}

    request._cached_json = (new_body, new_body)

    user_view.put(int(current_user.id))

    return {"status": "ok"}
