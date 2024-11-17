import hashlib

import redis
from app.db.session import SessionLocal
from app.conf.config import settings
from app.utils.file import delete_file

from .repository import thumbnail_repo


def clear_cache(thumbnails: list):
    db = SessionLocal()
    if thumbnails is None:
        thumbnails = thumbnail_repo.get_all(db)
    for thumbnail in thumbnails:
        hash_object = hashlib.sha224(
            f'{thumbnail.original} {thumbnail.width}x{thumbnail.height} {thumbnail.format}'.encode('ascii'))
        hex_dig = hash_object.hexdigest()
        redis_instance = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding='utf8',
        )
        redis_instance.delete(hex_dig)


def delete_thumbnails():
    db = SessionLocal()
    thumbnails = thumbnail_repo.get_all(db)
    clear_cache(thumbnails)
    for thumbnail in thumbnails:
        delete_file(thumbnail.thumbnail)
        thumbnail_repo.delete(db, db_obj=thumbnail)
    return len(thumbnails)
