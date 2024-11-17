import os
import uuid
import shutil
from typing import Optional, Tuple
from loguru import logger
from fastapi import UploadFile
from datetime import datetime
from PIL import Image
from fractions import Fraction

from app.conf.config import settings, structure_settings

__all__ = {
    'chunked_copy', 'upload_to',
    'convert_image', 'save_file',
    'delete_file', 'get_file_path'
}


async def chunked_copy(src: UploadFile, dst: str) -> None:
    """
    Save file in passed destination
    :param src:
    :param dst:
    :return:
    """
    await src.seek(0)
    with open(f'{dst}', "wb+") as buffer:
        while True:
            contents = await src.read(settings.FILE_CHUNK_SIZE)
            if not contents:
                logger.info(f"Src completely consumed\n")
                break
            logger.info(f"Consumed {len(contents)} bytes from Src file\n")
            buffer.write(contents)


def upload_to(filename: str, extension: str, file_dir: str = 'image/original') -> str:
    """
    Return path seperated by date, starts with slash
    :param filename:
    :param extension:
    :param file_dir:
    :return:
    """
    now: datetime = datetime.now()
    extension: str = extension.lower()
    parent_dir: str = f'{file_dir}/{now:%Y/%m/%d}'

    base_dir = structure_settings.MEDIA_DIR

    os.makedirs(f'{base_dir}/{parent_dir}', mode=0o777, exist_ok=True)

    return f"{parent_dir}/{filename}{extension}"


def image_crop_around(img: Image, xc, yc, w, h) -> Image:
    img_width, img_height = img.size  # Get dimensions
    left, right = xc - w / 2, xc + w / 2
    top, bottom = yc - h / 2, yc + h / 2
    left, top = round(max(0, left)), round(max(0, top))
    right, bottom = round(min(img_width - 0, right)), round(min(img_height - 0, bottom))
    return img.crop((left, top, right, bottom))


def image_crop_center(img: Image, w: int, h: int) -> Image:
    img_width, img_height = img.size
    left, right = (img_width - w) / 2, (img_width + w) / 2
    top, bottom = (img_height - h) / 2, (img_height + h) / 2
    left, top = round(max(0, left)), round(max(0, top))
    right, bottom = round(min(img_width - 0, right)), round(min(img_height - 0, bottom))
    return img.crop((left, top, right, bottom))


def resize_image(img: Image, w: int, h: int) -> Image:
    return img.resize((w, h))


def crop_resize(image, size, ratio):
    # crop to ratio, center
    w, h = image.size
    if w > ratio * h:  # width is larger then necessary
        x, y = (w - ratio * h) // 2, 0
    else:  # ratio*height >= width (height is larger)
        x, y = 0, (h - w / ratio) // 2
    image = image.crop((x, y, w - x, h - y))

    # resize
    if image.size > size:  # don't stretch smaller images
        image.thumbnail(size, Image.ANTIALIAS)
    return image


def convert_image(
        file_path: str,
        filename: str, file_format: Optional[str] = 'WEBP',
        width: Optional[int] = 255,
        height: Optional[int] = 255,
        ratio: Fraction = Fraction(255, 255),
        base_image_dir: Optional[str] = structure_settings.MEDIA_DIR,
) -> Tuple[str, bool]:
    """
    Convert image file to webp
    :param file_path:
    :param filename:
    :param file_format:
    :param width:
    :param height:
    :param ratio:
    :param base_image_dir:

    :return:
    """
    try:
        img = Image.open(f'{base_image_dir}/{file_path}')
        path = f'cache/{filename}'
        img = crop_resize(img, (width, height), ratio)

        base_dir = structure_settings.MEDIA_DIR
        img.save(f'{base_dir}/{path}', file_format)
        return f'{path}', True
    except FileNotFoundError as e:
        logger.info(f'{e} - 10333')
        return '', False
    except Exception as e:
        logger.info(f'{e} - 10334')
        return '', False


def save_file(
        file: UploadFile,
        file_dir: str,
        filename: Optional[str] = None,
) -> str:
    if filename is None:
        filename = uuid.uuid4().hex

    base, extension = os.path.splitext(file.filename)
    path = upload_to(filename, extension, file_dir)

    base_dir = structure_settings.MEDIA_DIR

    with open(f'{base_dir}/{path}', 'wb+') as fs:
        # content = file.file.read()
        file.file.seek(0)
        shutil.copyfileobj(file.file, fs)
        # fs.write(content)
    return path


def delete_file(path: str) -> bool:
    base_dir = structure_settings.MEDIA_DIR
    path = f'{base_dir}/{path}'
    if os.path.exists(path):
        os.remove(path)
        return True
    else:
        logger.info("The file does not exist - 10335")
        return False


def get_file_path(path: str):
    base_dir = structure_settings.MEDIA_DIR
    return f'/{base_dir}/{path}'
