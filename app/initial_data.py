import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    from app.db.init_db import init_db_sync
    from app.db.session import SessionLocal
    db = SessionLocal()
    init_db_sync(db)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
