import json
from os.path import isfile

from flask import current_app, Response
from flask_camp import allow, current_api


rule = "/health"


@allow("anonymous")
def get():
    """Returns information about the version of the API and the status
    of its components:

        - Git revision
        - PostgreSQL status
        - Last run of the ES syncer script
        - ES status
        - Number of documents indexed in ES
        - Redis status
        - Number of keys in Redis
        - Maintenance mode status

    """
    status = {"code": 200, "version": None}  # It's ITHUB_SHA in prod. WTF

    status["es"] = "ok"  # TODO legacy: remove this

    _add_database_status(status)
    _add_redis_status(status)
    _add_maintenance_mode_status(status)

    return Response(response=json.dumps(status), content_type="application/json", status=status["code"])


def _add_database_status(status):
    success = False

    try:
        current_api.database.session.execute("SELECT 1;")
        success = True
    except Exception:  # pylint:  disable=broad-except
        current_app.logger.exception("Database failed")
        status["code"] = 500

    status["pg"] = "ok" if success else "error"


def _add_redis_status(status):
    redis_keys = None
    success = False

    try:
        redis_keys = current_api.memory_cache.client.dbsize()
        success = True
    except Exception:  # pylint:  disable=broad-except
        current_app.logger.exception("Getting redis keys failed")

    status["redis"] = "ok" if success else "error"
    status["redis_keys"] = redis_keys


def _add_maintenance_mode_status(status):
    maintenance_mode = False
    maintenance_file = "maintenance_mode.txt"

    if isfile(maintenance_file):
        maintenance_mode = True
        current_app.logger.warning("service is in maintenance mode, remove %s to reenable." % maintenance_file)
        status["code"] = 404

    status["maintenance_mode"] = maintenance_mode
