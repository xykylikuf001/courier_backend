from fastapi import APIRouter

from app.contrib.account.api import api as account_api
from app.contrib.location.api import api as location_api
from app.contrib.file.api import api as file_api
from app.contrib.message.api import api as message_api

api = APIRouter()

api.include_router(account_api, tags=["account"])
api.include_router(location_api, tags=["location"], prefix="/location")
api.include_router(file_api, tags=["file"], prefix="/file")
api.include_router(message_api, tags=["message"], prefix="/message")
