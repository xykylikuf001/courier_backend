from enum import Enum
from app.core.enums import TextChoices
from app.utils.translation import gettext as _


class PaymentTypeChoices(TextChoices):
    withdraw = "withdraw"
    deposit = "deposit"
    send = "send"


class StorePaymentMethodChoices(TextChoices):
    """Represents if and how a payment should be stored in a payment gateway.

    The following store types are possible:
    - ON_SESSION - the payment is stored only to be reused when
    the customer is present in the checkout flow
    - OFF_SESSION - the payment is stored to be reused even if
    the customer is absent
    - NONE - the payment is not stored.
    """

    ON_SESSION = "ON_SESSION", _("On session")
    OFF_SESSION = "OFF_SESSION", _('Off session')
    NONE = "NONE", _('None')


class TransactionError(Enum):
    """Represents a transaction error."""

    INCORRECT_NUMBER = "INCORRECT_NUMBER"
    INVALID_NUMBER = "INVALID_NUMBER"
    INCORRECT_CVV = "INCORRECT_CVV"
    INVALID_CVV = "INVALID_CVV"
    INCORRECT_ZIP = "INCORRECT_ZIP"
    INCORRECT_ADDRESS = "INCORRECT_ADDRESS"
    INVALID_EXPIRY_DATE = "INVALID_EXPIRY_DATE"
    EXPIRED = "EXPIRED"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    DECLINED = "DECLINED"


class TransactionKindChoices(TextChoices):
    """Represents the type of transaction.

    The following transactions types are possible:
    - AUTH - an amount reserved against the customer's funding source. Money
    does not change hands until the authorization is captured.
    - VOID - a cancellation of a pending authorization or capture.
    - CAPTURE - a transfer of the money that was reserved during the
    authorization stage.
    - REFUND - full or partial return of captured funds to the customer.
    """

    EXTERNAL = "EXTERNAL", _("External reference")
    AUTH = "AUTH", _('Authorization')
    CHECK_STATUS = 'CHECK_STATUS', _('Check status')
    CAPTURE = "CAPTURE", _('Capture')
    CAPTURE_FAILED = "CAPTURE_FAILED"
    ACTION_TO_CONFIRM = "ACTION_TO_CONFIRM", _("Action to confirm")
    VOID = "VOID", _('Void')
    PENDING = "PENDING", _("Pending")
    REFUND = "REFUND", _('Refund')
    REFUND_ONGOING = "REFUND_ONGOING", _("Refund in progress")
    REFUND_FAILED = "REFUND_FAILED"
    REFUND_REVERSED = "REFUND_REVERSED"
    CONFIRM = "CONFIRM", _('Confirm')
    CANCEL = "CANCEL", _('Cancel')
    # FIXME we could use another status like WAITING_FOR_AUTH for transactions
    # Which were authorized, but needs to be confirmed manually by staff
    # eg. Braintree with "submit_for_settlement" enabled


class ChargeStatusChoices(TextChoices):
    """Represents possible statuses of a payment.

    The following statuses are possible:
    - NOT_CHARGED - no funds were take off the customer founding source yet.
    - PARTIALLY_CHARGED - funds were taken off the customer's funding source,
    partly covering the payment amount.
    - FULLY_CHARGED - funds were taken off the customer founding source,
    partly or completely covering the payment amount.
    - PARTIALLY_REFUNDED - part of charged funds were returned to the customer.
    - FULLY_REFUNDED - all charged funds were returned to the customer.
    """

    NOT_CHARGED = "NOT_CHARGED", _('Not charged')
    PENDING = "PENDING", _('Pending')
    PARTIALLY_CHARGED = "PARTIALLY_CHARGED", _('Partially charged')
    FULLY_CHARGED = "FULLY_CHARGED", _("Fully charged")
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", _('Partially refunded')
    FULLY_REFUNDED = "FULLY_REFUNDED", _('Fully refunded')
    REFUSED = "REFUSED", _('Refused')
    CANCELLED = "CANCELLED", _('Cancelled')


class CustomPaymentChoices(Enum):
    MANUAL = "MANUAL"
