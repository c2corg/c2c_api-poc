import os
from flask_camp.utils import SchemaValidator

# expose a decorator for schema validation
schema_validator = SchemaValidator(os.path.dirname(__file__))
schema = schema_validator.schema
