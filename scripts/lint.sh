#!/usr/bin/env bash


set -x

if ! command -v "poetry" > /dev/null; then
  if [ -f ./.venv/bin/python ]; then
      DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
  else [ -f ./venv/bin/python ];
      DEFAULT_PYTHON_VENV_PATH=./venv/bin/
  fi
  PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

  ${PYTHON_VENV_PATH}mypy app
  ${PYTHON_VENV_PATH}black app --check
  ${PYTHON_VENV_PATH}isort --recursive --check-only app
  ${PYTHON_VENV_PATH}flake8
else
  # Run tests
  poetry run mypy app
  poetry run black app --check
  poetry run isort --recursive --check-only app
  poetry run flake8
fi
