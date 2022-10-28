from flask import request
from flask_camp import allow
from flask_camp.views.account import user as user_view
from flask_login import current_user


rule = "/users/follow"


@allow("authenticated", allow_blocked=True)
def post():
    # convert v6 request to flask_camp request
    user_id = request.get_json()["user_id"]
    data = current_user.data
    follow = data["feed"]["follow"]

    if user_id in follow:
        return {"status": "ok"}

    follow.append(user_id)
    body = {"user": {"data": data}}
    request._cached_json = (body, body)
    return user_view.put(current_user.id)
