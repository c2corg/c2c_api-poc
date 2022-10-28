import time
from flask import request, current_app
from flask_camp import allow
from flask_camp.views.account import user_login
from werkzeug.exceptions import Unauthorized, Forbidden
from c2corg_api.security.discourse_client import get_discourse_client

# from c2corg_api.schemas import schema

rule = "/users/login"


# @schema("users_login.json")
@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    body = {
        "name_or_email": data.get("username"),
        "password": data.get("password"),
    }

    request._cached_json = (body, body)

    try:
        user = user_login.put()["user"]
    except Unauthorized as e:
        raise Forbidden() from e

    user["token"] = None
    user["expire"] = 14 * 24 * 3600 + int(round(time.time()))

    try:
        user["redirect_internal"] = get_discourse_client(current_app.config).redirect_without_nonce(user)
    except Exception:
        # Any error with discourse should not prevent login
        current_app.logger.exception("Error logging into discourse for %d", user["id"])

    return user
