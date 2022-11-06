from flask_login import current_user
from flask_camp._utils import JsonResponse

from c2corg_api.models import XREPORT_TYPE


def after_get_document(response: JsonResponse):
    document_data = response.data["document"]["data"]
    if document_data["type"] == XREPORT_TYPE:

        response.headers["Cache-Control"] = "private"

        if document_data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
            for field in ["author_status", "activity_rate", "age", "gender", "previous_injuries", "autonomy"]:
                document_data.pop(field, None)
