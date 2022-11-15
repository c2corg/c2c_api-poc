from flask import current_app
from werkzeug.exceptions import InternalServerError

from c2corg_api.security.discourse_client import get_discourse_client


def before_block_user(user):

    client = get_discourse_client(current_app.config)

    if user.blocked:
        # suspend account in Discourse (suspending an account prevents a login)
        try:
            client.suspend(user.id, 99999, "account blocked by moderator")  # 99999 days = 273 years
        except Exception as e:
            current_app.logger.exception("Suspending account in Discourse failed: %d", user.id)
            raise InternalServerError("Suspending account in Discourse failed") from e
    else:
        try:
            client.unsuspend(user.id)
        except Exception as e:
            current_app.logger.exception("Unsuspending account in Discourse failed: %d", user.id)
            raise InternalServerError("Unsuspending account in Discourse failed") from e
