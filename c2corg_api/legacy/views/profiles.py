from flask import request
from flask_camp import allow
from flask_camp.views.content import document as document_view
from werkzeug.exceptions import NotFound
from c2corg_api.models import USERPROFILE_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, LegacyView


class ProfilesView(DocumentCollectionView):
    rule = "/profiles"
    document_type = USERPROFILE_TYPE

    @allow("authenticated", allow_blocked=True)
    def get(self):
        return super().get()

    @allow("anonymous", "authenticated")
    def post(self):
        raise NotFound()  # just for test


class ProfileView(LegacyView):
    rule = "/profiles/<int:profile_id>"

    @allow("anonymous", "authenticated")
    def get(self, profile_id):
        result = document_view.get(profile_id)

        return self._get_legacy_doc(
            result.json["document"],
            lang=request.args.get("l"),
            cook_lang=request.args.get("cook"),
        )

    @allow("authenticated")
    def put(self, profile_id):
        body = request.get_json()

        new_body = self._from_legacy_doc(body, profile_id)

        request._cached_json = (new_body, new_body)

        result = document_view.post(profile_id)

        return result
