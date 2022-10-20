from flask import request
from flask_login import current_user
from flask_camp import allow
from flask_camp.models import User
from flask_camp.views.account import email_validation as email_validation_view

rule = "/users/validate_change_email/<string:token>"


@allow("anonymous", "authenticated", allow_blocked=True)
def post(token):

    user = User.get(_email_token=token)

    body = {"name": user.name, "token": token}

    request._cached_json = (body, body)

    return email_validation_view.post()
