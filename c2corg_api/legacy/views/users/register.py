from flask import request
from flask_camp import allow
from flask_camp.views.account import users
from flask_camp.models import User

rule = "/users/register"


@allow("anonymous")
def post():

    # convert v6 request to flask_camp request
    data = request.get_json()

    body = {
        "name": data.get("forum_username"),
        "email": data.get("email"),
        "password": data.get("password"),
        "ui_preferences": {
            "full_name": data.get("name"),
            "lang": data.get("lang", "fr"),
            "is_profile_public": False,
            "feed": {"areas": [], "activities": [], "langs": [], "followed_only": False, "follow": []},
        },
    }

    request._cached_json = (body, body)

    result = users.put()

    result["user"]["username"] = result["user"]["name"]
    result["user"]["forum_username"] = result["user"]["name"]
    result["user"]["email"] = User.get(id=result["user"]["id"])._email_to_validate
    result["user"]["name"] = result["user"]["ui_preferences"]["full_name"]

    return result["user"]
