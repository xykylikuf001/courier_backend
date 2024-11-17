from uuid import UUID

from typing import Optional, List, Literal
from pydantic import ValidationError, EmailStr

from fastapi import APIRouter, Depends, Query, Request, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError

from pydantic_core import ErrorDetails

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_sso.sso.google import GoogleSSO

from app.contrib.account import ServiceTypeChoices
from app.utils.security import lazy_jwt_settings
from app.routers.dependency import (
    get_async_db, get_current_user, get_commons,
    get_staff_user, get_token_payload, get_aioredis, get_redis
)
from app.core.schema import IResponseBase, IPaginationDataBase, CommonsModel
from app.utils.datetime.timezone import now
from app.utils.translation import gettext as _
from app.utils.jose import jwt
from app.conf.config import settings

from .tasks import send_email_verification_task, send_password_change_verification_task, send_reset_password_email_task
from .schema import (
    Token, UserVisible, UserBase, UserCreate,
    SignUpResult, SignUpIn, ProfilePasswordIn, TokenPayload, UserSessionVisible,
     VerifyToken, ProfileChangeEmail, ResetPassword
)
from .models import User
from .repository import user_repo, user_session_repo, external_account_repo
from .utils import rand_code

api = APIRouter()

sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    redirect_uri=settings.GOOGLE_REDIRECT_URI,
    allow_insecure_http=True,
)


async def create_verification_code(
        aioredis_instance, key: str, value: Optional[str] = None,
):
    expiration = await aioredis_instance.ttl(
        f"verify:{key}"
    )
    if expiration > settings.VERIFICATION_CODE_EXPIRE_SECONDS - 60:
        raise HTTPException(
            status_code=400,
            detail="Please wait one minute, before resend verification code"
        )

    if value is None:
        value = rand_code(settings.VERIFICATION_CODE_LENGTH)

    await aioredis_instance.setex(
        name=f"verify:{key}",
        value=value,
        time=settings.VERIFICATION_CODE_EXPIRE_SECONDS,
    )

    return value


async def check_verification_code(
        aioredis_instance, key: str, code: Optional[str] = None,
        check_code: Optional[bool] = True,
        expired_message: Optional[str] = _("Verification code does not exist or already expired"),
        invalid_message: Optional[str] = _("Invalid verification code")
):
    verification_code = await aioredis_instance.get(
        f"verify:{key}"
    )

    if not verification_code:
        raise HTTPException(status_code=400, detail=expired_message)
    elif check_code and verification_code != code:
        assert code is not None, "Code must not be None"
        raise HTTPException(status_code=400, detail=invalid_message)
    return verification_code


async def revoke_session(async_db, db_obj, aioredis_instance):
    revoked_at = now()

    session_key = f'session:{db_obj.id.hex}'

    await aioredis_instance.delete(session_key)

    result = await user_session_repo.update(async_db, db_obj=db_obj, obj_in={"revoked_at": revoked_at})
    return result


async def generate_auth_token(async_db, request, user):
    data = {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent"),
        "user_id": user.id,
    }
    session = await user_session_repo.create(async_db=async_db, obj_in=data)

    payload = lazy_jwt_settings.JWT_PAYLOAD_HANDLER(
        {
            'user_id': user.id,
            "email": user.email,
            'aud': lazy_jwt_settings.JWT_AUDIENCE,
            'jti': session.id.hex
        },
    )
    jwt_token = lazy_jwt_settings.JWT_ENCODE_HANDLER(payload)

    result = {
        'access_token': jwt_token,
        'token_type': 'bearer',
        "user": user
    }
    return result


@api.get("/auth/logout/", name="logout", response_model=IResponseBase[UserSessionVisible])
async def logout_from_account(
        aioredis_instance=Depends(get_aioredis),
        async_db: AsyncSession = Depends(get_async_db),

        token_payload: TokenPayload = Depends(get_token_payload),
):
    db_obj = await user_session_repo.get_by_params(async_db, params={"id": token_payload.jti, "revoked_at": None})

    result = await revoke_session(async_db, db_obj, aioredis_instance)

    return {
        "message": "You are successfully signed out",
        "data": result
    }


@api.post('/auth/get-token/', name='get-token', response_model=Token)
async def get_token(
        request: Request,
        data: OAuth2PasswordRequestForm = Depends(),
        async_db: AsyncSession = Depends(get_async_db),
) -> dict:
    """
    Get token from external api
    """
    user = await user_repo.authenticate(
        async_db=async_db,
        email=data.username,
        password=data.password,
    )
    if not user:
        raise RequestValidationError(
            [ErrorDetails(
                msg='Incorrect username or password',
                loc=("body", "username",),
                type='value_error',
                input=data.username
            )]
        )
    if not user.is_active:
        raise RequestValidationError(
            [ErrorDetails(
                msg='User is disabled',
                loc=("body", 'username',),
                type="value_error",
                input=data.username
            )]
        )
    return await generate_auth_token(async_db, request, user)


@api.post("/auth/verify-token/", name="verify-token", response_model=bool)
async def verify_token(
        token_in: VerifyToken
) -> bool:
    try:
        lazy_jwt_settings.JWT_DECODE_HANDLER(token_in.access_token)
    except (jwt.JWTError, ValidationError):
        return False
    return True


@api.get('/auth/sessions/', name='auth-sessions', response_model=List[UserSessionVisible])
async def get_user_sessions(
        user: "User" = Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
):
    obj_list = await user_session_repo.get_all(
        async_db,
        q={
            "user_id": user.id,
            "revoked_at": None
        }
    )
    return obj_list


@api.get('/auth/sessions/revoke-all/', name='auth-session-revoke-all', response_model=IResponseBase[str])
async def revoke_all_sessions(
        token_payload: TokenPayload = Depends(get_token_payload),
        async_db: AsyncSession = Depends(get_async_db),
        aioredis_instance=Depends(get_aioredis),

):
    expressions = [
        user_session_repo.model.id != token_payload.jti
    ]
    obj_list = await user_session_repo.get_all(async_db, q={"revoked_at": None}, offset=0, expressions=expressions)
    for user_session in obj_list:
        await revoke_session(async_db, user_session, aioredis_instance)

    return {
        "message": "All sessions revoked",
        "data": ""
    }


@api.get('/auth/sessions/{obj_id}/revoke/', name='auth-session-revoke',
         response_model=IResponseBase[UserSessionVisible])
async def revoke_single_session(
        obj_id: UUID,
        async_db: AsyncSession = Depends(get_async_db),
        aioredis_instance=Depends(get_aioredis),
        token_payload: TokenPayload = Depends(get_token_payload),
):
    if obj_id == token_payload.jti:
        raise HTTPException(status_code=400, detail="Can not revoke current session")

    db_obj = await user_session_repo.get(async_db, obj_id=obj_id)
    result = await revoke_session(async_db, db_obj, aioredis_instance)

    return {
        "message": "Session revoked",
        "data": result
    }


@api.get("/auth/me/", response_model=UserVisible, name='me')
async def get_me(
        user=Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
):
    db_obj = await user_repo.get(async_db, obj_id=user.id)
    return db_obj


@api.post('/auth/sign-up/', name='sign-up', response_model=IResponseBase[SignUpResult])
async def sign_up(
        request: Request,
        obj_in: SignUpIn,
        async_db: AsyncSession = Depends(get_async_db),
        aioredis_instance=Depends(get_aioredis),
) -> dict:
    if obj_in.policy is False:
        raise RequestValidationError(
            [ErrorDetails(
                msg=_("Policy must be agreed"),
                loc=("body", "policy",),
                type='value_error',
                input=obj_in.policy
            )]
        )

    is_exist = await user_repo.exists(async_db, params={"email": obj_in.email})

    if is_exist:
        raise RequestValidationError(
            [ErrorDetails(
                msg="User with this email already exist",
                loc=("body", "email",),
                type='value_error',
                input=obj_in.email
            )]
        )

    user = await user_repo.create(
        async_db=async_db,
        obj_in={
            "email": obj_in.email,
            "name": obj_in.name,
            "password": obj_in.password
        }
    )

    verification_code = await create_verification_code(
        aioredis_instance,
        key=f'{obj_in.email}-{ServiceTypeChoices.email.value}',
    )

    send_email_verification_task.delay(email=user.email, code=verification_code)

    result = await generate_auth_token(async_db, request, user)
    if obj_in.subscription:
        # Todo cover subscription logic
        pass
    return {
        "data": result,
        "message": "Thanks for sign-up! Nice journey!"
    }


@api.get("/auth/google/callback/", name="auth-by-google", response_model=IResponseBase[Token])
async def auth_by_google(
        request: Request,
        code: str = Query(...),
        scope: str = Query(...),
        authuser: str = Query(...),
        prompt: str = Query(...),
        async_db: AsyncSession = Depends(get_async_db),
):
    with sso:
        openid = await sso.verify_and_process(request)
    # return user
    db_obj = await user_repo.first(async_db, params={"email": openid.email})
    if not db_obj:
        password = rand_code(8)

        prepared_data = {
            "email": openid.email,
            "name": f'{openid.first_name} {openid.last_name}',
            "email_verified_at": now(),
            "password": password
        }
        db_obj = await user_repo.create(
            async_db, obj_in=prepared_data
        )
        await external_account_repo.create(
            async_db,
            obj_in={
                "user_id": db_obj.id,
                "account_id": openid.id,
                "username": openid.email,
                "service_type": ServiceTypeChoices.google
            }
        )
    result = await generate_auth_token(async_db, request, db_obj)

    return {
        "data": result,
        "message": "Thanks for sign-up! Nice journey!"
    }




@api.post('/auth/email/verify/send/', name='auth-email-verify-send', response_model=IResponseBase[str])
async def send_email_verification_code(
        email: EmailStr = Form(...),
        user=Depends(get_current_user),
        aioredis_instance=Depends(get_aioredis)
):
    verification_code = await create_verification_code(
        aioredis_instance,
        key=f'{email}-{ServiceTypeChoices.email.value}',
    )

    send_email_verification_task.delay(email=user.email, code=verification_code)

    return {
        "data": user.email,
        "message": _("Verification code send to your email")
    }


@api.get('/auth/email/verify/{code}/confirm/', name='auth-email-verify', response_model=IResponseBase[str])
async def verify_email_with_code(
        code: str,
        user=Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
        aioredis_instance=Depends(get_aioredis),
):
    if user.email is None:
        raise HTTPException(status_code=400, detail=_("You do not have email yet."))
    if user.email_verified_at:
        raise HTTPException(status_code=400, detail=_("You email already verified."))

    await check_verification_code(
        aioredis_instance,
        key=f'{user.email}-{ServiceTypeChoices.email.value}',
        code=code,
    )

    await user_repo.raw_update(
        async_db, expressions=(User.id == user.id,),
        obj_in={"email_verified_at": now()}
    )

    return {
        "message": _("Email verified"),
        "data": ""
    }


@api.get(
    '/user/', name='user-list', response_model=IPaginationDataBase[UserVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_user_list(
        async_db: AsyncSession = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        user_id: Optional[UUID] = None,
        search: Optional[str] = Query(None, max_length=255),
        order_by: Optional[Literal["created_at", "-created_at"]] = "-created_at"
):
    options = None
    expressions = []
    if user_id:
        expressions.append(User.id == user_id)
    if search:
        expressions.append(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )
    obj_list = await user_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        q={"is_superuser": False},
        options=options,
        order_by=[order_by]
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": obj_list
    }


@api.get(
    "/user/count/", name="user-count",
    response_model=int,
    dependencies=[Depends(get_staff_user)]
)
async def count_users(
        async_db: AsyncSession = Depends(get_async_db)
):
    return await user_repo.count(async_db, params={"is_superuser": False})


@api.post(
    '/user/create/', name="user-create",
    response_model=IResponseBase[UserVisible],
    status_code=201,
)
async def account_create(
        obj_in: UserCreate,
        async_db: AsyncSession = Depends(get_async_db),
        user=Depends(get_staff_user),
):
    is_exist = await user_repo.exists(async_db, params={"email": obj_in.email})
    if is_exist:
        raise RequestValidationError(
            [ErrorDetails(
                msg="User with this username already exist",
                loc=("body", "email",),
                type='value_error',
                input=obj_in.email
            )]
        )

    if obj_in.is_staff and user.is_superuser is False:
        raise RequestValidationError(
            [ErrorDetails(
                msg="Only admin can add staff member",
                loc=("body", "isStaff",),
                type='value_error',
                input=obj_in.is_staff
            )]
        )

    result = await user_repo.create(async_db, obj_in=obj_in.model_dump())
    return {
        "message": "User created",
        "data": result
    }


@api.get(
    "/user/{obj_id}/detail/", name='user-detail',
    response_model=UserVisible,
    dependencies=[Depends(get_staff_user)],
)
async def get_single_user(
        obj_id: UUID,
        async_db: AsyncSession = Depends(get_async_db),

):
    return await user_repo.get(async_db, obj_id=obj_id)


@api.patch(
    "/user/{obj_id}/update/", name='user-update', response_model=IResponseBase[UserVisible],

)
async def update_user(
        obj_id: UUID,
        obj_in: UserBase,
        async_db: AsyncSession = Depends(get_async_db),
        user=Depends(get_staff_user),
):
    db_obj = await user_repo.get(async_db, obj_id=obj_id)
    if (db_obj.is_staff or obj_in.is_staff) and user.is_superuser is False:
        raise RequestValidationError(
            [ErrorDetails(
                msg="Only admin can edit staff member or set permission",
                loc=("body", "isStaff",),
                type='value_error',
                input=obj_in.is_staff
            )]
        )
    data = obj_in.model_dump(exclude_unset=True)

    if obj_in.email and obj_in.email != db_obj.email:
        is_exist = await user_repo.exists(async_db, params={"email": obj_in.email})
        if is_exist:
            raise RequestValidationError(
                [ErrorDetails(
                    msg="User with this email already exist",
                    loc=("body", "email",),
                    type='value_error',
                    input=obj_in.email
                )]
            )

    result = await user_repo.update(async_db, db_obj=db_obj, obj_in=data)
    return {
        "message": "User updated",
        "data": result
    }


@api.delete(
    "/user/{obj_id}/delete/", name='user-delete',
    status_code=204,

)
async def delete_user(
        obj_id: UUID,
        async_db: AsyncSession = Depends(get_async_db),
        user=Depends(get_staff_user),
):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    await user_repo.remove(async_db, expressions=[User.id == obj_id])


@api.patch("/profile/update/", name="user-profile-update", response_model=IResponseBase[UserVisible])
async def user_profile_update(
        name: str = Form(..., max_length=255),
        user: User = Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
        redis_instance=Depends(get_redis),
) -> dict:
    db_obj = await user_repo.get(async_db, obj_id=user.id)
    data = {
        "name": name,
    }
    result = await user_repo.update(
        async_db=async_db,
        db_obj=db_obj,
        obj_in=data
    )
    for k in redis_instance.scan_iter(f"session-{user.id.__str__()}:*"):
        redis_instance.delete(k)

    return {
        "message": "Profile updated",
        "data": result
    }


@api.post("/profile/change-password/", name="user-profile-change-password", response_model=IResponseBase[str])
async def user_profile_password_change(
        obj_in: ProfilePasswordIn,
        user: User = Depends(get_current_user),

        aioredis_instance=Depends(get_aioredis),
        async_db: AsyncSession = Depends(get_async_db),
):
    await check_verification_code(
        aioredis_instance,
        key=f'{user.email}-{ServiceTypeChoices.email.value}-password',
        code=obj_in.code,
    )

    check_pass = user_repo.verify_password(user, obj_in.old_password)
    if not check_pass:
        raise RequestValidationError(
            [ErrorDetails(
                msg="Invalid current password",
                loc=("body", "oldPassword",),
                type='value_error',
                input=obj_in.old_password
            )]
        )
    await user_repo.raw_update(async_db, expressions=(User.id == user.id,), obj_in={"password": obj_in.password})

    return {
        "message": "Password changed!",
        "data": ""
    }


@api.get('/profile/change-password/code/', name='user-profile-change-password-code', response_model=IResponseBase[str])
async def user_profile_password_change_send_code(
        user: User = Depends(get_current_user),
        aioredis_instance=Depends(get_aioredis),
):
    if user.email is None:
        raise HTTPException(status_code=400, detail=_("Sorry, you do not have verified email yet"))

    verification_code = await create_verification_code(
        aioredis_instance, key=f'{user.email}-{ServiceTypeChoices.email.value}-password'
    )

    send_password_change_verification_task.delay(email=user.email, code=verification_code)
    return {
        "message": "Password change code sent to your email",
        "data": ""
    }


@api.post(
    '/profile/set-email/', name='user-profile-set-email', response_model=IResponseBase[UserVisible]
)
async def set_user_profile_email(
        email: EmailStr = Form(...),
        code: str = Form(...),
        user: User = Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
        redis_instance=Depends(get_redis),
        aioredis_instance=Depends(get_aioredis),

):
    if user.email is not None:
        raise HTTPException(status_code=400, detail=_("Sorry, your profile already have email"))
    await check_verification_code(
        aioredis_instance,
        key=f'{email}-{ServiceTypeChoices.email.value}',
        code=code,
    )

    result = await user_repo.raw_update(
        async_db, obj_in={'email': email, "email_verified_at": now()},
        expressions=(User.id == user.id,)
    )

    for k in redis_instance.scan_iter(f"session-{user.id.__str__()}:*"):
        redis_instance.delete(k)

    return {
        "message": _("Profile email updated"),
        "data": result
    }


@api.post('/profile/change-email/', name="user-profile-change-email", response_model=IResponseBase[str])
async def change_profile_email(
        obj_in: ProfileChangeEmail,
        async_db: AsyncSession = Depends(get_async_db),
        user: User = Depends(get_current_user),
        aioredis_instance=Depends(get_aioredis),
        redis_instance=Depends(get_redis),

):
    if user.email is None:
        raise HTTPException(status_code=400, detail=_("Sorry, you do not have verified email yet"))

    old_email = user.email

    await check_verification_code(
        aioredis_instance,
        key=f'{user.email}-{ServiceTypeChoices.email.value}',
        code=obj_in.code,
        expired_message=_("Verification code for current email does not exist or already expired"),
        invalid_message=_("Invalid verification code for current email")
    )

    await check_verification_code(
        aioredis_instance,
        key=f'{obj_in.email}-{ServiceTypeChoices.email.value}',
        code=obj_in.email_code,
        expired_message=_("Verification code for new email does not exist or already expired"),
        invalid_message=_("Invalid verification code for new email")
    )

    result = await user_repo.raw_update(
        async_db, expressions=(User.id == user.id,),
        obj_in={"email": obj_in.email, "email_verified_at": now()}
    )

    await external_account_repo.create(
        async_db, obj_in={
            "user_id": user.id,
            "account_id": old_email,
            "username": old_email,
            "is_active": False,
            "service_type": ServiceTypeChoices.email
        }
    )

    for k in redis_instance.scan_iter(f"session-{user.id.__str__()}:*"):
        redis_instance.delete(k)

    return {
        "message": _("Profile email changed successfully"),
        "data": ""
    }


@api.post("/profile/forgot-password/", name="user-profile-forgot-password", response_model=IResponseBase[str])
async def forgot_password(
        email: EmailStr = Form(...),
        aioredis_instance=Depends(get_aioredis),
        async_db: AsyncSession = Depends(get_async_db),
) -> dict:
    user = await user_repo.first(async_db, params={"email": email})

    if not user:
        return {
            "data": email,
            "message": _("Password reset link sent to your email!")
        }

    elif not user.is_active:
        raise HTTPException(status_code=400, detail=_("Your account is disabled"))

    expiration = await aioredis_instance.ttl(
        f"{user.id}_{ServiceTypeChoices.email}-p_forgot"
    )
    if expiration > settings.VERIFICATION_CODE_EXPIRE_SECONDS - 60:
        raise HTTPException(
            status_code=400,
            detail=_("Please wait one minute, before resend verification code")
        )

    verification_code = await create_verification_code(
        aioredis_instance,
        key=f'{email}-{ServiceTypeChoices.email.value}-p_forgot'
    )

    send_reset_password_email_task.delay(email=user.email, code=verification_code)

    return {
        "data": email,
        "message": _("Password reset link sent to your email!")
    }


@api.post("/profile/reset-password/", name="user-profile-reset-password", response_model=IResponseBase[str])
async def reset_password(
        obj_in: ResetPassword,
        aioredis_instance=Depends(get_aioredis),
        async_db: AsyncSession = Depends(get_async_db),
) -> dict:
    user = await user_repo.first(async_db, {"email": obj_in.email})
    if not user:
        raise HTTPException(
            detail=_("User does not exist with this email"),
            status_code=400
        )
    elif user.is_active is False:
        raise HTTPException(status_code=400, detail=_("Your account is disabled"))
    elif user.is_staff is True:
        raise HTTPException(status_code=400, detail=_("Not this time bro :)"))

    await check_verification_code(
        aioredis_instance,
        key=f'{obj_in.email}-{ServiceTypeChoices.email.value}-p_forgot',
        code=obj_in.code,
    )

    await user_repo.raw_update(
        async_db=async_db,
        expressions=(User.id == user.id,),
        obj_in={'password': obj_in.password}
    )

    return {
        "message": _("User password reset"),
        'data': ""
    }
