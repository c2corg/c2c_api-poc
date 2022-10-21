class DocumentIdList:
    def __init__(self, _list):
        self._list = _list

    def append(self, item):
        if isinstance(item, (int)):
            self._list.append(item)
        else:
            self._list.append(item.document_id)


class User:
    def __init__(self) -> None:
        self._user = None
        self.feed_filter_areas = None

    @classmethod
    def from_user(cls, user):
        result = cls()
        result._user = user
        result.feed_filter_areas = DocumentIdList(result._user.ui_preferences["feed"]["areas"])

        return result

    @property
    def username(self):
        return self._user.name

    @property
    def email_validated(self):
        return self._user.email_is_validated

    @property
    def lang(self):
        return self._user.ui_preferences["lang"]

    @property
    def password(self):
        return self._user.password_hash

    @property
    def email(self):
        return self._user._email

    @property
    def validation_nonce(self):
        return self._user._login_token

    @property
    def blocked(self):
        return self._user.blocked

    @blocked.setter
    def blocked(self, value):
        self._user.blocked = value

    @property
    def email_to_validate(self):
        return self._user._email_to_validate

    @property
    def name(self):
        return self._user.ui_preferences["full_name"]

    @name.setter
    def name(self, value):
        self._user.ui_preferences["full_name"] = value

    @property
    def forum_username(self):
        return self._user.name

    @property
    def is_profile_public(self):
        return self._user.ui_preferences["is_profile_public"]

    @property
    def feed_filter_activities(self):
        return self._user.ui_preferences["feed"]["activities"]

    @feed_filter_activities.setter
    def feed_filter_activities(self, value):
        self._user.ui_preferences["feed"]["activities"] = value

    @property
    def feed_filter_langs(self):
        return self._user.ui_preferences["feed"]["langs"]

    @feed_filter_langs.setter
    def feed_filter_langs(self, value):
        self._user.ui_preferences["feed"]["langs"] = value
