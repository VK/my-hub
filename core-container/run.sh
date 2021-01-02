#!/usr/bin/env bash

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