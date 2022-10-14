from flask import request
from flask_camp import allow
from flask_camp.views.account import users

from c2corg_api.schemas import schema

rule = "/users/register"


@schema("users_register.json")
@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    body = {
        "name": data.get("username"),
        "email": data.get("email"),
        "password": data.get("password"),
    }

    if "lang" in data:
        body["lang"] = data["lang"]

    request._cached_json = (body, body)

    result = users.put()

    return result["user"]
