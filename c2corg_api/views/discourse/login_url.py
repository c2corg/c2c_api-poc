from flask import current_app
from flask_login import current_user
from flask_camp import allow

from c2corg_api.security.discourse_client import get_discourse_client

rule = "/discourse/login_url"


@allow("authenticated")
def get():
    client = get_discourse_client(current_app.config)

    return {"status": "ok", "url": client.redirect_without_nonce(current_user)}
