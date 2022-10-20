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
    user["forum_username"] = user["name"]
    user["is_profile_public"] = False  # TODO : save this info in profile page

    return user


@allow("authenticated", allow_blocked=True)
def post():
    body = request.get_json()

    new_body = {"password": body["currentpassword"]}

    if "email" in body:
        new_body["email"] = body["email"]

    request._cached_json = (new_body, new_body)

    user_view.post(int(current_user.id))

    return {"status": "ok"}
