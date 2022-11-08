from flask_login import current_user
from werkzeug.exceptions import Forbidden

from c2corg_api.models._core import BaseModelHooks


class TopoMap(BaseModelHooks):
    def on_creation(self, version):
        if not current_user.is_moderator:
            raise Forbidden()

    def on_new_version(self, old_version, new_version):
        if not current_user.is_moderator:
            raise Forbidden()
