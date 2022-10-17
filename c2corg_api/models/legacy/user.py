class User:
    def __init__(self) -> None:
        self._user = None

    @classmethod
    def from_user(cls, user):
        result = cls()
        result._user = user

        return result

    @property
    def email_validated(self):
        return self._user.email_is_validated

    @property
    def lang(self):
        return self._user.ui_preferences["lang"]
