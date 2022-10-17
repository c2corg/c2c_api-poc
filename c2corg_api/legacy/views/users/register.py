from flask import request
from flask_camp import allow
from flask_camp.views.account import users
from flask_camp.models import User

from c2corg_api.schemas import schema

rule = "/users/register"


@schema("users_register.json")
@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    body = {
        "name": data.get("forum_username"),
        "email": data.get("email"),
        "password": data.get("password"),
    }

    if "lang" in data:
        body["lang"] = data["lang"]

    request._cached_json = (body, body)

    result = users.put()

    result["user"]["username"] = result["user"]["name"]
    result["user"]["forum_username"] = result["user"]["name"]
    result["user"]["email"] = User.get(id=result["user"]["id"])._email_to_validate

    return result["user"]
