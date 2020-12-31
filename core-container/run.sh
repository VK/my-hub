#!/usr/bin/env bash

case "$1" in
  start)
    python /assure_airflow_db.py
    airflow initdb
    exec airflow webserver -p 8888 &
    exec airflow scheduler &
    #exec python /setup_routes.py &
    exec jupyterhub -f /jupyterhub_config.py
    ;;
  *)
    # Everything else
    exec "$@"
    ;;
esac