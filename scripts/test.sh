#!/usr/bin/env bash


set -e
set -x

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  # Run tests
  ${PYTHON_VENV_PATH}pytest --cov=app --cov-report=term-missing tests "${@}"
else
  # Run tests
#  poetry run pytest --cov=app --cov-report=term-missing tests "${@}"  -s -k test_get_my_network_stats_api
#  poetry run pytest --cov=app --cov-report=term-missing tests
  poetry run pytest  -s -k test_get_my_network_stats_api
fi


