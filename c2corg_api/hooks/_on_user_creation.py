from c2corg_api.hooks._tools import check_user_name
from c2corg_api.models import create_user_profile


def on_user_creation(user):
    check_user_name(user.name)
    create_user_profile(user, ["fr"])
