from flask import request
from flask_camp import allow
from flask_camp.views.account import user as user_view
from flask_login import current_user


rule = "/users/unfollow"


@allow("authenticated", allow_blocked=True)
def post():
    # convert v6 request to flask_camp request
    user_id = request.get_json()["user_id"]
    data = current_user.data
    follow = data["feed"]["follow"]

    if user_id not in follow:
        return {"status": "ok"}

    follow.remove(user_id)
    body = {"data": data}
    request._cached_json = (body, body)
    return user_view.post(current_user.id)
