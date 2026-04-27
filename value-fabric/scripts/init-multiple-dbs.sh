#!/bin/bash
# init-multiple-dbs.sh
#
# Creates additional PostgreSQL databases on first container boot.
# Triggered by the Docker postgres entrypoint via /docker-entrypoint-initdb.d/.
#
# Usage: Set POSTGRES_MULTIPLE_DATABASES env var to a comma-separated list
# of database names. The primary database (POSTGRES_DB) is created automatically
# by the postgres image; this script creates the additional ones.
#
# Example:
#   POSTGRES_MULTIPLE_DATABASES=ingestion,ground_truth
#
# Reference: https://github.com/mrts/docker-postgresql-multiple-databases

set -e
set -u

function create_user_and_database() {
    local database=$1
    echo "  Creating database '$database' if it does not exist"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        SELECT 'CREATE DATABASE $database'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$database')\gexec
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_user_and_database $db
    done
    echo "Multiple databases created."
fi
