#! /usr/bin/env bash


set -e

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  # Let the DB start
  ${PYTHON_VENV_PATH}python -m app.celeryworker_pre_start
  ${PYTHON_VENV_PATH}celery -A app.worker flower --port=5555
else
  # Let the DB start
  poetry run python -m app.celeryworker_pre_start

  poetry run celery -A app.worker flower --port=5555
fi

