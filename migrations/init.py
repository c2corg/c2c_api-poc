from contextlib import contextmanager
from time import perf_counter
from sqlalchemy import create_engine


@contextmanager
def catchtime() -> float:
    start = perf_counter()
    yield
    r = perf_counter() - start
    print(f"Execution time: {r:.4f} secs")


db_host = "localhost"
db_port = "5432"
db_user = "www-data"
db_password = "www-data"
db_name = "c2corg"

database_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(database_uri)

with catchtime():
    rows = engine.execute("SELECT * FROM guidebook.documents_versions ORDER BY id ASC")
    for i, row in enumerate(rows):
        if i % 1000 == 0:
            print(i, row)

print(i)
