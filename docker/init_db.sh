#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER flask_camp_user WITH PASSWORD 'flask_camp_user';
	CREATE DATABASE flask_camp;
	GRANT ALL PRIVILEGES ON DATABASE flask_camp TO flask_camp_user;
EOSQL
