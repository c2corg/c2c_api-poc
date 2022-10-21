from copy import deepcopy
from flask import request
from flask_login import current_user
from flask_camp import allow
from flask_camp.views.account import current_user as current_user_view
from flask_camp.views.account import user as user_view

rule = "/users/preferences"


@allow("authenticated", allow_blocked=True)
def get():
    return {"status": "ok"}
