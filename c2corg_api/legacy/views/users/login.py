from flask import request
from flask_camp import allow
from flask_camp.views.account import user_login

# from flask_camp.models import User

# from c2corg_api.schemas import schema

rule = "/users/login"


# @schema("users_login.json")
@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    body = {
        "name": data.get("username"),
        "password": data.get("password"),
    }

    request._cached_json = (body, body)

    user = user_login.post()["user"]

    user["token"] = None

    return user
