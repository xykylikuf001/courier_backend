from typing import Optional
from typing_extensions import Annotated

from pydantic import Field, BeforeValidator

from app.core.schema import VisibleBase, ChoiceBase, BaseModel
from app.conf.config import settings, structure_settings
from app.contrib.file import ContentTypeChoices, FileTypeChoices


def assemble_file_url(v, info) -> str:
    if v:
        return v
    values = info.data
    file_host = values.get('file_host')
    file_path = values.get('file_path')

    if not file_host:
        file_host = f'{settings.IMAGE_HOST}/{structure_settings.MEDIA_DIR}'

    return f'{file_host}/{file_path}'


FileUrl = Annotated[Optional[str], BeforeValidator(assemble_file_url)]


class FileBase(BaseModel):
    caption: Optional[str] = Field(None, max_length=500)


class FileVisible(VisibleBase):
    id: int
    file_type: ChoiceBase[FileTypeChoices] = Field(alias="fileType")
    file_path: str = Field(alias="filePath")
    file_host: Optional[str] = Field(alias="fileHost")

    content_type: ChoiceBase[ContentTypeChoices] = Field(alias="contentType")
    file_url: FileUrl = Field(None, alias="fileUrl", validate_default=True)
    poster: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None
