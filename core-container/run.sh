#!/usr/bin/env bash

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