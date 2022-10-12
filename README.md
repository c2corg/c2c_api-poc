POC of a simplified -but full featured- API for camptocamp.org


## Install dev env

*Requirements: [python](https://www.python.org/downloads/) and [docker](https://docs.docker.com/engine/install/)*

```bash
./scripts/install_dev_env.sh
```

This command will create a [python virtual environments](https://docs.python.org/3/tutorial/venv.html), upgrade pip and setup tools and then install the project in edition mode. Windows users, you must use `.\scripts\install_dev_env.bat` (to be tested though).

## Contribute

Before starting edition/tests, you must activate the environment and have a [redis](https://redis.io/) on port 6379 and a [postgresql](https://www.postgresql.org/) on port 5432. It can be easily achievied with:

```bash
source venv/bin/activate   # activate the environment (if it's not automatic, see IDE section)
flask_camp dev_env         # start redis and postgresql
flask_camp init_db         # init the database, only if you want to run the app
```

The first run may take a while :coffee:

## Run locally

```bash
flask run
```

:rocket: http://localhost:5000 :rocket: 

If it's not done, run `flask_camp init_db` to init the database (be carefull, the test suite totally clean it on each run)

## Run test suite

```bash
pytest
```

And a little bit more friendly, the test tab in VScode! 

💡 The test suite totally clean the database it on each run. You may need to re-run `flask_camp init_db` before re-running the app. Though, your modification should be tested using the test suite, so it may not happen so often. 💡

## IDE

### VSCode

The repo is configured to be working out-of-the box with [VSCode](https://code.visualstudio.com/) with python/pylance extension. But feel free to use/add another conf for your favorite IDE.

### Pycharm

TODO
