import os
from flask_camp._schemas import SchemaValidator

# expose a decorator for schema validation
schema = SchemaValidator(os.path.dirname(__file__)).schema
