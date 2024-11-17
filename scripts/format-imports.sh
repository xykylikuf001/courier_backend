#!/bin/sh -e


set -x

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  # Sort imports one per line, so autoflake can remove unused imports
  ${PYTHON_VENV_PATH}isort --recursive  --force-single-line-imports --apply app
else
  # Sort imports one per line, so autoflake can remove unused imports
  poetry run isort --recursive  --force-single-line-imports --apply app
fi

sh ./scripts/format.sh
