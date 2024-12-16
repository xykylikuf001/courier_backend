from starlette.status import HTTP_302_FOUND
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette_i18n import gettext_lazy as _
from app.core.exceptions import HTTP404
from app.routers.dependency import get_db, get_authenticated_user, get_commons, get_user_with_verified_email

from sqlalchemy.orm import Session
from app.contrib.auth.models import User
from app.core.request import Request 
from app.core.routing import APIRoute
from .exceptions import PaymentError
from .gateways.turkmenpay.plugin import TurkmenPayGatewayPlugin
from .repository import payment_repo
from .gateway import check_payment_status, capture

router = APIRouter(route_class=APIRoute)


@router.get('/{obj_id}/check-payment/', response_class=RedirectResponse, name='payment-check')
def check_payment(
        request: Request,
        obj_id: str,
        user: User = Depends(get_authenticated_user),
        db: Session = Depends(get_db),

) -> RedirectResponse:
    payment = payment_repo.get_by_params(db=db, params={'id': obj_id})
    if not payment:
        raise HTTP404(_('Payment does not exist'))
    payment_gateway = TurkmenPayGatewayPlugin()
    try:
        __, txn = capture(
            db=db,
            payment=payment,
            payment_gateway=payment_gateway,
        )
    except PaymentError as e:
        payment_repo.update(db=db, db_obj=payment, obj_in={'is_active': False})
        flash(request, str(e), 'warning')
    else:
        order_repo.update(db=db, db_obj=payment.order, obj_in={'is_paid': True})
        # payment_repo.update(db=db, db_obj=payment, obj_in={'is_active': False})
        flash(request, str(_('Order successfully paid')))
    return RedirectResponse(request.url_for('frontend:order-detail-page', checkout_token=payment.order.checkout_token),
                            status_code=HTTP_302_FOUND)
