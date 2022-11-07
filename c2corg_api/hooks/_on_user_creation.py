from c2corg_api.hooks._tools import check_user_name
from c2corg_api.models.userprofile import UserProfile


def on_user_creation(user):
    check_user_name(user.name)
    UserProfile.create(user, ["fr"])
