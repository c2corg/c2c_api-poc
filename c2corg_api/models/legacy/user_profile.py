from flask_camp.models import User, Document

USERPROFILE_TYPE = "profiles"


class UserProfile:
    def __init__(self, user_id) -> None:
        self._profile_page = Document.get(id=user_id)
        self._user = User.get(id=user_id)
        self._versions = list(self._profile_page.versions)

    @property
    def versions(self):
        return self._versions
