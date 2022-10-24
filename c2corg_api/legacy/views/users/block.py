from flask import request
from flask_camp import allow
from flask_camp.views.account import block_user as block_user_view

rule = "/users/block"


@allow("moderator")
def post():
    data = request.get_json()
    body = {"blocked": True, "comment": "Default comment"}
    request._cached_json = (body, body)

    return block_user_view.post(data["user_id"])
