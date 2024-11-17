from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()


@router.get('/', tags=['default'], name='root')
async def root_path():
    return "Hello, from api root!!!"


@router.get('/favicon.ico', response_class=FileResponse, name='favicon', tags=['favicon'])
async def favicon() -> str:
    return 'static/images/logo/favicon.ico'
