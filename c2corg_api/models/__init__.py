USERPROFILE_TYPE = "profile"
AREA_TYPE = "area"

VALIDATION_EXPIRE_DAYS = 3


def get_default_user_profile_data(user, categories):
    return {
        "type": USERPROFILE_TYPE,
        "user_id": user.id,
        "locales": [{"title": user.name, "lang": "fr"}, {"title": user.name, "lang": "en"}],
        "categories": categories,
        "areas": [],
        "name": user.ui_preferences["full_name"],
    }


# TODO: move to legacy folder (only used in legacy test and legacy interface)
def get_defaut_user_ui_preferences(full_name, lang):
    return {
        "full_name": full_name,
        "lang": lang,
        "is_profile_public": False,
        "feed": {"areas": [], "activities": [], "langs": [], "followed_only": False, "follow": []},
    }
