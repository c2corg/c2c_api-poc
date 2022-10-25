from flask import request
from flask_camp import allow
from flask_camp.views.account import block_user as block_user_view
from werkzeug.exceptions import BadRequest

rule = "/users/unblock"


@allow("moderator")
def post():
    data = request.get_json()

    if data["user_id"] <= 0:
        raise BadRequest(f"user_id can't be negative")

    body = {"blocked": False, "comment": "Default comment"}
    request._cached_json = (body, body)

    return block_user_view.post(data["user_id"])
