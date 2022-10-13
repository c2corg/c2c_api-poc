from flask import request

from flask_camp import allow
from c2corg_api.views.markdown import cook


rule = "/cooker"


@allow("anonymous")  # TODO : must be authenticated ?
def post():
    """
    This service is a stateless service that returns HTML values.

    * Input and output are dictionaries
    * keys are keep unmodified
    * values are parsed from markdown to HTML, only if key is not in
      c2corg_api.views.markdown.NOT_MARKDOWN_PROPERTY
    """
    return cook(request.get_json())
