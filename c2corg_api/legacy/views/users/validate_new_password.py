from flask import request
from flask_camp import current_api, allow
from flask_camp.models import User
from flask_login import login_user
from werkzeug.exceptions import NotFound

rule = "/users/validate_new_password/<string:token>"


@allow("anonymous")
def post(token):
    user = User.get(_login_token=token, with_for_update=True)

    if user is None:
        raise NotFound()

    login_user(user)

    body = request.get_json()
    user.set_password(body["password"])

    current_api.database.session.commit()

    return {"status": "ok"}
