#! /usr/bin/env bash

RUN_PRESTART=${RUN_PRESTART:-false}


# ...do something interesting...
if [ "$RUN_PRESTART" = true ] ; then
  if ! command -v "poetry" > /dev/null; then
    if [ -f ./.venv/bin/python ]; then
        DEFAULT_PYTHON_VENV_PATH=./.venv/bin/
    else [ -f ./venv/bin/python ];
        DEFAULT_PYTHON_VENV_PATH=./venv/bin/
    fi
    PYTHON_VENV_PATH=${DEFAULT_PYTHON_VENV_PATH:-$DEFAULT_PYTHON_VENV_PATH}

    echo "Let the DB start"
    ${PYTHON_VENV_PATH}python -m app.backend_pre_start

    # Run migrations
    ${PYTHON_VENV_PATH}alembic upgrade head

    echo "Create initial data in DB"
    ${PYTHON_VENV_PATH}python -m app.initial_data
  else
    echo "Let the DB start"
    poetry run python -m app.backend_pre_start

    # Run migrations
    poetry run alembic upgrade head

    echo "Create initial data in DB"
    poetry run python -m app.initial_data
  fi
fi


