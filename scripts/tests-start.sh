#! /usr/bin/env bash


set -e

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  # Run tests
  ${PYTHON_VENV_PATH}python  -m app.tests_pre_start
else
  # Run tests
  poetry run python  -m app.tests_pre_start
fi

bash scripts/test.sh "$@"
