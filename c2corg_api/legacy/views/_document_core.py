from flask import request
from flask_camp import allow
from flask_camp.views.content import documents as documents_view, document as document_view, version as version_view
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest

from c2corg_api.legacy.converter import convert_to_legacy_doc, convert_from_legacy_doc


class LegacyView:
    @staticmethod
    def _get_preferred_locale(preferred_lang, locales):
        if preferred_lang in locales:
            return locales[preferred_lang]

        langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

        for lang in langs_priority:
            if lang in locales:
                return locales[lang]

        return None  # raise ?

    @staticmethod
    def _from_legacy_doc(body, uri_document_id):

        if "document" not in body:
            raise BadRequest()

        return {
            "comment": body.get("message", "default comment"),
            "document": convert_from_legacy_doc(body["document"], expected_document_id=uri_document_id),
        }

    @classmethod
    def _get_legacy_doc(cls, document, collection_view=False, preferred_lang=None, lang=None, cook_lang=None):

        result = convert_to_legacy_doc(document)

        locales = document["data"]["locales"]

        if lang is not None:
            if lang in locales:
                result["locales"] = [locales[lang]]
            else:
                result["locales"] = []

        if preferred_lang is not None:
            result["locales"] = [cls._get_preferred_locale(preferred_lang, locales)]

        if cook_lang is not None:
            cooked_locales = document["cooked_data"]["locales"]
            result["locales"] = [cls._get_preferred_locale(cook_lang, locales)]
            result["cooked"] = cls._get_preferred_locale(cook_lang, cooked_locales)

        if collection_view:
            if "geometry" in result:
                del result["geometry"]

        return result


class DocumentCollectionView(LegacyView):
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
            "total": result["count"],
            "documents": [
                self._get_legacy_doc(
                    document,
                    collection_view=True,
                    preferred_lang=request.args.get("pl"),
                )
                for document in result["documents"]
            ],
        }


class DocumentView(LegacyView):
    @allow("anonymous", "authenticated")
    def get(self, document_id):
        result = document_view.get(document_id)

        return self._get_legacy_doc(
            result.json["document"],
            lang=request.args.get("l"),
            cook_lang=request.args.get("cook"),
        )


class VersionView(LegacyView):
    @allow("anonymous", "authenticated")
    def get(self, document_id, lang, version_id):
        r = version_view.get(version_id)
        return {
            "document": self._get_legacy_doc(r["document"], cook_lang=lang),
            "previous_version_id": None,  # TODO
            "next_version_id": None,  # TODO
            "version": {
                "comment": "creation",
                "name": r["document"]["user"]["name"],
                "user_id": r["document"]["user"]["id"],
                "version_id": r["document"]["version_id"],
                "written_at": r["document"]["timestamp"],
            },
        }
