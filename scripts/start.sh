#! /usr/bin/env sh

set -e

if [ -f ./app/main.py ]; then
    DEFAULT_MODULE_NAME=app.main
elif [ -f ./main.py ]; then
    DEFAULT_MODULE_NAME=main
fi
MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

if [ -f ./app/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=./app/gunicorn_conf.py
elif [ -f ./app/app/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=./app/app/gunicorn_conf.py
else
    DEFAULT_GUNICORN_CONF=./gunicorn_conf.py
fi
export GUNICORN_CONF=${GUNICORN_CONF:-$DEFAULT_GUNICORN_CONF}
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}

# If there's a prestart.sh script in the /app directory or other path specified, run it before starting
PRE_START_PATH=${PRE_START_PATH:-./scripts/prestart.sh}
echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "There is no script $PRE_START_PATH"
fi
echo "$APP_MODULE"

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  # Start Gunicorn
   ${PYTHON_VENV_PATH}gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"

else
   poetry run gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"
fi
