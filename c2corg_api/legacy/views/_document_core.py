from flask import request
from flask_camp import allow, current_api
from flask_camp.views.content import documents as documents_view, document as document_view, version as version_view
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from c2corg_api.legacy.converter import convert_to_legacy_doc, convert_from_legacy_doc


class DocumentCollectionView:
    document_type = NotImplemented

    def get(self):
        http_args = request.args.to_dict()
        http_args["document_type"] = self.document_type
        request.args = ImmutableMultiDict(http_args)

        if "offset" in request.args:
            try:
                _ = int(request.args["offset"])
            except ValueError as e:
                raise BadRequest() from e

        result = documents_view.get()

        return {
            "total": result.data["count"],
            "documents": [
                convert_to_legacy_doc(
                    document,
                    collection_view=True,
                    preferred_lang=request.args.get("pl"),
                )
                for document in result.data["documents"]
            ],
        }

    @allow("authenticated")
    def post(self):
        if not request.is_json:
            raise UnsupportedMediaType()

        legacy_doc = request.get_json()

        # document_id is allowed in old model, even if it does not make sense
        legacy_doc.pop("document_id", None)

        new_model = convert_from_legacy_doc(legacy_doc, document_type=self.document_type, previous_data={})

        body = {"document": new_model, "comment": "creation"}

        request._cached_json = (body, body)

        r = documents_view.post()

        return convert_to_legacy_doc(r.data["document"])


class DocumentView:
    document_type = NotImplemented

    @allow("anonymous", "authenticated")
    def get(self, document_id):
        result = document_view.get(document_id)

        result.data = convert_to_legacy_doc(
            result.data["document"],
            lang=request.args.get("l"),
            cook_lang=request.args.get("cook"),
        )

        return result

    @allow("authenticated")
    def put(self, document_id):
        body = request.get_json()

        if "document" not in body:
            raise BadRequest()

        old_version = current_api.get_document(document_id)
        if old_version is None:
            raise NotFound()

        if document_id != body["document"].get("document_id", None):
            raise BadRequest("Id in body does not match id in URI")

        new_body = {
            "comment": body.get("message", "default comment"),
            "document": convert_from_legacy_doc(
                body["document"],
                document_type=self.document_type,
                previous_data=old_version["data"],
            ),
        }

        request._cached_json = (new_body, new_body)

        result = document_view.post(document_id)

        return result


class VersionView:
    @allow("anonymous", "authenticated")
    def get(self, document_id, lang, version_id):
        response = version_view.get(version_id)
        document = response.data["document"]
        legacy_content = {
            "document": convert_to_legacy_doc(document, cook_lang=lang),
            "previous_version_id": None,  # TODO
            "next_version_id": None,  # TODO
            "version": {
                "comment": "creation",
                "name": document["user"]["name"],
                "user_id": document["user"]["id"],
                "version_id": document["version_id"],
                "written_at": document["timestamp"],
            },
        }

        response.data = legacy_content
        response.add_etag = True

        return response
