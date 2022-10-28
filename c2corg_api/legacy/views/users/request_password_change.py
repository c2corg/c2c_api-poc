from flask import request
from flask_camp import allow
from flask_camp.models import User
from flask_camp.views.account import reset_password
from werkzeug.exceptions import Forbidden


rule = "/users/request_password_change"


@allow("anonymous")
def post():
    email = request.get_json()["email"]

    user = User.get(_email=email)

    if user is None:  # do not let hacker crawl our base
        fake_user = User()
        fake_user.set_login_token()

        return {"status": "ok", "expiration_date": fake_user.login_token_expiration_date.isoformat()}

    if user.blocked:
        raise Forbidden()

    return reset_password.put()
