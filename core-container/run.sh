#!/usr/bin/env bash

python /assure_airflow_db.py
cd /jupyterhub

case "$1" in
  start)
    supervisord
    exec jupyterhub -f /jupyterhub_config.py
    ;;
  *)
    # Everything else
    exec "$@"
    ;;
esac