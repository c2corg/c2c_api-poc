from flask import request, current_app
from flask_camp import current_api
from flask_camp.models import User
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, NotFound

from c2corg_api.hooks._tools import check_user_name
from c2corg_api.security.discourse_client import get_discourse_client


def on_user_update(user: User, sync_sso=True):

    # as now, flask_camp does not allow to modify user name. To be discussed (maybe a modo action)
    # v6 API allows it, so we do that here
    data = request.get_json()

    if "name" in data:
        user.name = data["name"]
        check_user_name(user.name)
        try:
            current_api.database.session.flush()
        except IntegrityError as e:
            raise BadRequest("Name or email already exists") from e

    follow = list(set(user.data["feed"]["follow"]))
    user.data["feed"]["follow"] = follow  # remove duplicates

    if len(follow) != 0:
        real_user_ids = [r[0] for r in current_api.database.session.query(User.id).filter(User.id.in_(follow)).all()]
        if len(follow) != len(real_user_ids):
            raise NotFound(f"{follow} {real_user_ids}")

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)
