#!/bin/sh
set -eu
export FUR_APP_PASSWORD="$(cat "$FUR_APP_PASSWORD_FILE")"
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 <<'SQL'
\getenv fur_password FUR_APP_PASSWORD
\getenv fur_database POSTGRES_DB
SELECT format('CREATE ROLE fur LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'fur_password') WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fur') \gexec
SELECT format('ALTER DATABASE %I OWNER TO fur', :'fur_database') \gexec
GRANT USAGE, CREATE ON SCHEMA public TO fur;
SQL
unset FUR_APP_PASSWORD
