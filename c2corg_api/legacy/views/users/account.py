from flask_camp import allow
from flask_camp.views.account import current_user


rule = "/users/account"


@allow("authenticated", allow_blocked=True)
def get():
    result = current_user.get()
    user = result["user"]
    user["forum_username"] = user["name"]
    user["is_profile_public"] = False  # TODO : save this info in profile page

    return user
