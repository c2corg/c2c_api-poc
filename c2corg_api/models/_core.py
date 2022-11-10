from flask_camp._utils import JsonResponse


class BaseModelHooks:
    def after_get_document(self, response: JsonResponse):
        ...

    def on_creation(self, version):
        ...

    def on_new_version(self, old_version, new_version):
        ...

    def cook(self, document: dict, get_document):
        ...
