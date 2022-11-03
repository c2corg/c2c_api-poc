from flask import request
from flask_camp import allow
from flask_camp.views.account import users
from flask_camp.models import User

from c2corg_api.hooks._tools import check_user_name
from c2corg_api.legacy.models.user import get_defaut_user_data

rule = "/users/register"


@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    if "forum_username" in data:
        check_user_name(data.get("forum_username"))

    body = {
        "user": {
            "name": data.get("forum_username"),
            "email": data.get("email"),
            "password": data.get("password"),
            "data": get_defaut_user_data(full_name=data.get("name"), lang=data.get("lang", "fr")),
        }
    }

    request._cached_json = (body, body)

    result = users.post()

    result["user"]["username"] = result["user"]["name"]
    result["user"]["forum_username"] = result["user"]["name"]
    result["user"]["email"] = User.get(id=result["user"]["id"])._email_to_validate
    result["user"]["name"] = data.get("name")

    return result["user"]
