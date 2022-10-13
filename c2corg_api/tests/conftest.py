import logging
import sys

from c2corg_api.app import create_app


def pytest_configure(config):
    if config.getoption("-v") > 1:
        logging.getLogger("sqlalchemy").addHandler(logging.StreamHandler(sys.stdout))
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)

    if not config.option.collectonly:
        tested_app, tested_api = create_app(TESTING=True)

        # clean previous uncleaned state
        # do not perform this on collect, editors that automatically collect tests on file change
        # may break current test session
        with tested_app.app_context():

            # why not using tested_api.database.drop_all()?
            # because in some case, a table is not known by the ORM
            # for instance, run test A that define a custom table, stop it during execution (the table is not removed)
            # then run only test B. Table defined in test A is not known

            sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            rows = tested_api.database.session.execute(sql)
            names = [name for name, in rows]
            if len(names) != 0:
                tested_api.database.session.execute(f"DROP TABLE {','.join(names)} CASCADE;")
                tested_api.database.session.commit()

            tested_api.database.create_all()

        tested_api.memory_cache.flushall()
