from typing import TYPE_CHECKING, Optional
from fastapi.encoders import jsonable_encoder
import magic

from app.db.repository import CRUDBase
from app.utils.file import save_file, delete_file
from app.core.enums import Choices
from app.contrib.file import FileTypeChoices

from .models import File, Thumbnail
from .exceptions import UpsupportedFileType

if TYPE_CHECKING:
    from fastapi import UploadFile
    from sqlalchemy.ext.asyncio import AsyncSession

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska'}
ALLOWED_AUDIO_TYPES = {'audio/mpeg', 'audio/wav', 'audio/aac'}
ALLOWED_PDF_TYPES = {'application/pdf'}


def get_content_type(file):
    return magic.Magic(mime=True).from_buffer(file.read(1024))


def is_image(content_type):
    return content_type in ALLOWED_IMAGE_TYPES


def is_pdf(content_type):
    return content_type in ALLOWED_PDF_TYPES


def is_video(content_type):
    return content_type in ALLOWED_VIDEO_TYPES


def is_mp3(content_type):
    return content_type in ALLOWED_AUDIO_TYPES


def is_gif(content_type):
    return content_type == 'image/gif'


def get_file_content_type(upload_file: "UploadFile") -> FileTypeChoices:
    content_type = upload_file.content_type
    if is_image(content_type):
        return FileTypeChoices.image
    elif is_pdf(content_type):
        return FileTypeChoices.pdf
    elif is_video(content_type):
        return FileTypeChoices.video
    elif is_mp3(content_type):
        return FileTypeChoices.mp3
    elif is_gif(content_type):
        return FileTypeChoices.gif
    raise UpsupportedFileType("Unsupported file type.")


class CRUDFile(CRUDBase[File]):
    async def create_with_file(
            self,
            async_db: "AsyncSession",
            upload_file: "UploadFile",
            obj_in: Optional[dict] = None,
            commit: Optional[bool] = True,
            flush: Optional[bool] = False,
    ) -> File:
        if obj_in is None:
            data = dict()
        else:
            data = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
        file_type = get_file_content_type(upload_file)

        original_file = save_file(upload_file, file_dir=file_type.value)
        try:
            data = data | {
                'file_type': file_type.value,
                'file_path': original_file,
            }
            db_obj = await self.create(async_db, obj_in=data, commit=commit, flush=flush)

        except Exception as e:
            delete_file(original_file)
            raise e
        return db_obj

    async def update_with_file(
            self,
            async_db: "AsyncSession",
            db_obj: File,
            upload_file: "UploadFile",
            obj_in: Optional[dict] = None,
    ):

        if obj_in is None:
            data = dict()
        else:
            data = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
        file_type = get_file_content_type(upload_file)

        new_image_path = save_file(upload_file, file_dir=file_type.value)
        old_image_path = db_obj.file_path
        data['file_path'] = new_image_path
        try:
            db_obj = await self.update(async_db, db_obj=db_obj, obj_in=data)
        except Exception as e:
            delete_file(new_image_path)
            raise e
        else:
            delete_file(old_image_path)
        return db_obj

    async def delete_with_file(self, async_db: "AsyncSession", db_obj: File) -> File:
        file_path = db_obj.file_path
        await self.delete(async_db, db_obj=db_obj)
        delete_file(file_path)
        return db_obj


class CRUDThumbnail(CRUDBase[Thumbnail]):
    pass


file_repo = CRUDFile(File)
thumbnail_repo = CRUDThumbnail(Thumbnail)
