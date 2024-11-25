from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

router = APIRouter()


@router.get('/', tags=['default'], name='root')
async def root_path():
    return "Hello, from api root!!!"


@router.get('/favicon.ico', response_class=FileResponse, name='favicon', tags=['favicon'])
async def favicon() -> str:
    return 'static/images/logo/favicon.ico'


@router.get('/android-release/{apk_version}/', response_class=FileResponse, name='release', tags=['release'])
async def android_release(
        apk_version: str
) -> str:
    return f'release/android/{apk_version}/release-apk.zip'
