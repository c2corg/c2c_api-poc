from flask import request
from flask_camp import allow


rule = "/profiles"


@allow("authenticated", allow_blocked=True)
def get():
    return "ok"
