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

    @property
    def password(self):
        return self._user.password_hash

    @property
    def email(self):
        return self._user._email

    @property
    def validation_nonce(self):
        return self._user._login_token
