from flask import request
from flask_camp import allow
from flask_camp.views.account import user as user_view
from flask_login import current_user


rule = "/users/follow"


@allow("authenticated", allow_blocked=True)
def post():
    # convert v6 request to flask_camp request
    user_id = request.get_json()["user_id"]
    ui_preferences = current_user.ui_preferences
    follow = ui_preferences["feed"]["follow"]

    if user_id in follow:
        return {"status": "ok"}

    follow.append(user_id)
    body = {"ui_preferences": ui_preferences}
    request._cached_json = (body, body)
    return user_view.post(current_user.id)
