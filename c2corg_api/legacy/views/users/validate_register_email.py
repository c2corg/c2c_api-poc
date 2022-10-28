from flask import request

from flask_camp import allow
from flask_camp.views.account import email_validation
from flask_camp.models import User


rule = "/users/validate_register_email/<string:token>"


@allow("anonymous")
def post(token):

    user = User.get(_email_token=token)

    body = {"name": user.name, "token": token}
    request._cached_json = (body, body)

    return email_validation.put()
