from app.db.repository import CRUDBase

from .models import Payment, Transaction, PaymentAttachment


class CRUDPayment(CRUDBase[Payment]):
    pass


class CRUDTransaction(CRUDBase[Transaction]):
    pass


class CRUDPaymentAttachment(CRUDBase[PaymentAttachment]):
    pass


payment_repo = CRUDPayment(Payment)
transaction_repo = CRUDTransaction(Transaction)
payment_attachment_repo = CRUDPaymentAttachment(PaymentAttachment)
