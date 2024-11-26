import os
import psutil
import time
import platform
from typing import Literal

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse

from app.utils.file import save_file, delete_file

from app.core.schema import IResponseBase
from .dependency import get_staff_user

router = APIRouter()

ALLOWED_ZIP_TYPES = {'application/zip', 'application/x-zip-compressed', 'multipart/x-zip'}


@router.get('/system/', name='system-detail', response_model=dict,
            dependencies=[Depends(get_staff_user)], tags=["system"])
async def system_detail(
):
    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get memory info
    virtual_memory = psutil.virtual_memory()
    total_memory = virtual_memory.total
    used_memory = virtual_memory.used
    free_memory = virtual_memory.available

    # Get disk usage
    disk_usage = psutil.disk_usage('/')
    total_disk = disk_usage.total
    used_disk = disk_usage.used
    free_disk = disk_usage.free

    # Get system uptime
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    uptime_humanized = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))

    # Get OS information
    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()

    return {
        "cpu_usage": f"{cpu_usage}%",
        "memory": {
            "total": f"{total_memory / (1024 ** 3):.2f} GB",
            "used": f"{used_memory / (1024 ** 3):.2f} GB",
            "free": f"{free_memory / (1024 ** 3):.2f} GB"
        },
        "disk": {
            "total": f"{total_disk / (1024 ** 3):.2f} GB",
            "used": f"{used_disk / (1024 ** 3):.2f} GB",
            "free": f"{free_disk / (1024 ** 3):.2f} GB"
        },
        "uptime": {
            "seconds": uptime_seconds,
            "human_readable": uptime_humanized
        },
        "os": {
            "name": os_name,
            "version": os_version,
            "release": os_release
        }
    }


def is_zip(content_type):
    return content_type in ALLOWED_ZIP_TYPES


def validate_zip_file(upload_file: "UploadFile") -> bool:
    content_type = upload_file.content_type
    if is_zip(content_type):
        return True
    raise HTTPException(detail="Unsupported file type.", status_code=400)


@router.get('/', tags=['default'], name='root')
async def root_path():
    return "Hello, from api root!!!"


@router.get('/favicon.ico', response_class=FileResponse, name='favicon', tags=['favicon'])
async def favicon() -> str:
    return 'static/images/logo/favicon.ico'


@router.get(
    '/android-release/{apk_version}/', response_class=FileResponse, name='release', tags=['release']
)
async def android_release(
        apk_version: str,
) -> FileResponse:
    if not os.path.exists(f'release/android/{apk_version}/release-apk.zip'):
        raise HTTPException(status_code=404, detail="File does not exist")
    return FileResponse(
        path=f'release/android/{apk_version}/release-apk.zip',
        filename=f"android-{apk_version}-release-apk.zip"
    )


@router.post(
    '/release/upload/', response_model=IResponseBase[str], name='release-upload', tags=['release'],
    dependencies=[Depends(get_staff_user)]
)
async def upload_release(
        upload_file: UploadFile = File(...),
        version: str = Form(..., max_length=10),
        release_os: Literal["android", "ios"] = Form(...),
):
    is_zip_file = validate_zip_file(upload_file)
    filename = "release-apk"

    if release_os == "ios":
        filename = "release-ios.zip"

    full_path = f"release/{release_os}/{version}/{filename}.zip"

    # Check if the file exists
    if os.path.exists(full_path):
        raise HTTPException(status_code=400, detail="File already exists")

    original_file = save_file(
        upload_file,
        base_dir="release",
        file_dir=f"{release_os}/{version}",
        filename=filename,
        extension=".zip",
        with_datetime=False
    )

    return {
        "message": "Release uploaded",
        "data": ""
    }


@router.get(
    '/release/file/list/',
    response_model=dict,
    name='release-file-list',
    tags=['release'],
    dependencies=[Depends(get_staff_user)]
)
async def list_nested_files():
    base_dir = "release"

    # Check if the directory exists
    if not os.path.exists(base_dir):
        raise HTTPException(status_code=404, detail="Directory not found")

    nested_structure = {}

    try:
        # Walk through the directory
        for root, dirs, files in os.walk(base_dir):
            relative_path = os.path.relpath(root, base_dir)
            if relative_path == ".":
                relative_path = "/"

            nested_structure[relative_path] = {
                "directories": dirs,
                "files": files,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading directory: {str(e)}")

    return nested_structure


@router.get(
    '/release/file/delete/', response_model=IResponseBase[str],
    name='release-file-delete', tags=["release"],
    dependencies=[Depends(get_staff_user)]
)
async def delete_release_file(
        version: str = Query(..., max_length=10),
        release_os: Literal["android", "ios"] = Query(...),
):
    filename = "release-apk"

    if release_os == "ios":
        filename = "release-ios.zip"

    full_path = f"{release_os}/{version}/{filename}.zip"
    # Check if the directory exists
    if not os.path.exists(f'release/{full_path}'):
        raise HTTPException(status_code=404, detail="File does not exist")

    delete_file(full_path, base_dir="release")
    return {
        "message": "File deleted",
        "data": full_path
    }
