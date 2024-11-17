#!/bin/sh -e


set -x

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  ${PYTHON_VENV_PATH}autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app --exclude=__init__.py
  ${PYTHON_VENV_PATH}black app
  ${PYTHON_VENV_PATH}isort --recursive --apply app
else
  # Sort imports one per line, so autoflake can remove unused imports
  poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app --exclude=__init__.py
  poetry run black app
  poetry run isort --recursive --apply app

fi


