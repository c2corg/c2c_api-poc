USERPROFILE_TYPE = "profile"

VALIDATION_EXPIRE_DAYS = 3


def get_default_user_profile_data(user, categories):
    return {
        "type": USERPROFILE_TYPE,
        "user_id": user.id,
        "locales": [{"title": user.name, "lang": "fr"}, {"title": user.name, "lang": "en"}],
        "categories": categories,
    }
