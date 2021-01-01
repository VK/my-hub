#!/usr/bin/env bash

case "$1" in
  start)
    python /assure_airflow_db.py
    airflow db init
    if [ `airflow users list | grep admin | wc -l` -lt 1 ] 
    then
      airflow users create -u admin -p admin -e admin@admin.de -f admin -l admin -r Admin
    fi
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