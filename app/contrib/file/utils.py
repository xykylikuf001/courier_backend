import json
import logging
import hashlib
import uuid
import redis

from typing import Optional

from fractions import Fraction

from app.conf.config import settings
from app.db.session import SessionLocal
from app.utils.file import delete_file, convert_image

from .repository import thumbnail_repo



def get_image_thumbnail(
        image_path: str, width: Optional[int] = 255, height: Optional[int] = 255,
        file_format: Optional[str] = 'WEBP', crop: Optional[str] = 'center', placeholder: Optional[int] = 255) -> str:

    if image_path:
        redis_instance = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding='utf8',
        )
        db = SessionLocal()
        hash_object = hashlib.sha224(f'{image_path} {width}x{height} {file_format}'.encode('ascii'))
        hex_dig = hash_object.hexdigest()
        thumbnail = redis_instance.get(hex_dig, )
        if not thumbnail:
            data = {
                'original': image_path,
                'width': width,
                'height': height,
                'format': file_format,
                'crop': crop,
            }
            thumbnail_image = thumbnail_repo.get_by_params(db=db, params=data)
            if thumbnail_image is None:
                thumbnail_name = f'{uuid.uuid4()}.{file_format.lower()}'
                thumbnail_path, is_success = convert_image(
                    image_path,
                    filename=thumbnail_name,
                    file_format=file_format,
                    width=width,
                    height=height,
                    ratio=Fraction(width, height),
                )
                if is_success:
                    data['thumbnail'] = thumbnail_path
                    try:
                        thumbnail_image = thumbnail_repo.create(db=db, obj_in=data)
                    except Exception:
                        delete_file(thumbnail_path)
                    thumbnail = {'thumbnail': thumbnail_image.thumbnail}
                else:
                    print(f'File does not exist: {image_path}')
            else:
                thumbnail = {'thumbnail': thumbnail_image.thumbnail}
                redis_instance.set(hex_dig, json.dumps(thumbnail.copy()))
        if thumbnail:
            if isinstance(thumbnail, str):
                thumbnail = json.loads(thumbnail)
            return f'/media/{thumbnail.get("thumbnail")}'
    return f'/static/{settings.PLACEHOLDER_IMAGES.get(placeholder)}'
