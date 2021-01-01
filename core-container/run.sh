#!/usr/bin/env bash

case "$1" in
  start)
    python /assure_airflow_db.py
    /home/admin/.local/bin/airflow db init
    if [ `/home/admin/.local/bin/airflow users list | grep admin | wc -l` -lt 1 ] 
    then
      /home/admin/.local/bin/airflow users create -u admin -p admin -e admin@admin.de -f admin -l admin -r Admin
    fi
    exec /home/admin/.local/bin/airflow webserver -p 8888 &
    exec /home/admin/.local/bin/airflow scheduler &
    #exec python /setup_routes.py &
    exec jupyterhub -f /jupyterhub_config.py
    ;;
  *)
    # Everything else
    exec "$@"
    ;;
esac