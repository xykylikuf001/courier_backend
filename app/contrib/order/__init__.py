from app.core.enums import TextChoices
from app.utils.translation import gettext_lazy as _


class OrderStatusChoices(TextChoices):
    draft = "draft", _("Draft")  # fully editable, not finalized order created by staff users
    unconfirmed = (
        "unconfirmed", _("Unconfirmed")  # order created by customers when confirmation is required
    )
    confirmed = "confirmed", _("Confirmed")
    on_process = "on_process", _("On process")
    unfulfilled = "unfulfilled", _("Unfulfilled")  # order with no items marked as fulfilled
    partially_fulfilled = (
        "partially fulfilled", _("Partially fulfilled")  # order with some items marked as fulfilled
    )
    fulfilled = "fulfilled", _("Fulfilled")  # order with all items marked as fulfilled

    partially_returned = (
        "partially_returned", _("Partially returned")  # order with some items marked as returned
    )
    returned = "returned", _("Returned")  # order with all items marked as returned
    canceled = "canceled", _("Canceled")  # permanently canceled order
    expired = "expired", _("Expired")  # order marked as expired
    rejected = "rejected", _("Rejected")


class ShippingMethodChoices(TextChoices):
    regular = "regular", _("Regular")
    express = "express", _("Express")


class OrderEventChoices(TextChoices):
    """the different order event types."""
    confirmed = "confirmed", _("Order was confirmed")
    draft_created = "draft_created", _("The draft order was created")
    draft_created_from_replace = "draft_created_from_replace", _("The draft order with replace lines was created")

    placed = "placed", _("The order was placed")
    placed_from_draft = "placed_from_draft", _("The draft order was placed")

    canceled = "canceled", _("The order was canceled")
    expired = "expired", _("The order was automatically expired")

    order_marked_as_paid = "order_marked_as_paid", _("The order was manually marked as fully paid")
    order_fully_paid = "order_fully_paid", _("The order was fully paid")
    order_replacement_created = "order_replacement_created", _("The draft order was created based on this order.")

    order_discount_added = "order_discount_added", _("New order discount applied to this order.")
    order_discount_automatically_updated = (
        "order_discount_automatically_updated",
        _("Order discount was automatically updated after the changes in order.")
    )
    order_discount_updated = "order_discount_updated", _("Order discount was updated for this order.")
    order_discount_deleted = "order_discount_deleted", _("Order discount was deleted for this order.")
    order_line_discount_updated = "order_line_discount_updated", _("Order line was discounted.")
    order_line_discount_removed = "order_line_discount_removed", _("The discount for order line was removed.")

    updated_address = "updated_address", _("The address from the placed order was updated")

    email_sent = "email_sent", _("The email was sent")

    payment_authorized = "payment_authorized", _("The payment was authorized")
    payment_captured = "payment_captured", _("The payment was captured")
    payment_refunded = "payment_refunded", _("The payment was refunded")
    payment_voided = "payment_voided", _("The payment was voided")
    payment_failed = "payment_failed", _("The payment was failed")

    transaction_event = "transaction_event", _("The transaction event")
    transaction_charge_requested = "transaction_charge_requested", _("The charge requested for transaction")
    transaction_refund_requested = "transaction_refund_requested", _("The refund requested for transaction")
    transaction_cancel_requested = "transaction_cancel_requested",_("The cancel requested for transaction")
    transaction_mark_as_paid_failed = "transaction_mark_as_paid_failed", _("The mark as paid failed for transaction")

    external_service_notification = "external_service_notification", _("Notification from external service")

    invoice_requested = "invoice_requested", _("An invoice was requested")
    invoice_generated = "invoice_generated", _("An invoice was generated")
    invoice_updated = "invoice_updated", _("An invoice was updated")
    invoice_sent = "invoice_sent", _("An invoice was sent")

    fulfillment_canceled = "fulfillment_canceled", _("A fulfillment was canceled")
    # fulfillment_restocked_items = "fulfillment_restocked_items",_("The items of the fulfillment were restocked")
    fulfillment_fulfilled_items = "fulfillment_fulfilled_items", _("Some items were fulfilled")
    fulfillment_refunded = "fulfillment_refunded", _("Some items were refunded")
    fulfillment_returned = "fulfillment_returned", _("Some items were returned")
    fulfillment_replaced = "fulfillment_replaced", _("Some items were replaced")
    fulfillment_awaits_approval = "fulfillment_awaits_approval", _("Fulfillments awaits approval")
    TRACKING_UPDATED = "tracking_updated", _("The fulfillment's tracking code was updated")

    note_added = "note_added", _("A note was added to the order")
    note_updated = "note_updated", _("A note was updated in the order")
    other = "other", _("An unknown order event containing a message")


class FulfillmentStatusChoices(TextChoices):
    fulfilled = "fulfilled", _("Fulfilled")  # group of products in an order marked as fulfilled
    refunded = "refunded", _("Refunded")  # group of refunded products
    returned = "returned", _("Returned")  # group of returned products
    refunded_and_returned = (
        "refunded_and_returned", _("Refunded and returned")  # group of returned and replaced products
    )
    replaced = "replaced", _("Replaced")  # group of replaced products
    canceled = "canceled", _("Canceled")  # fulfilled group of products in an order marked as canceled
    rejected = "rejected", _("Rejected")  # fulfilled group of products in an order marked as rejected
    waiting_for_approval = (
        "waiting_for_approval", _("Waiting for approval")  # group of products waiting for approval
    )


class OrderChargeStatusChoices(TextChoices):
    """Determine the current charge status for the order.

    An order is considered overcharged when the sum of the
    transactionItem's charge amounts exceeds the value of
    `order.total` - `order.totalGrantedRefund`.
    If the sum of the transactionItem's charge amounts equals
    `order.total` - `order.totalGrantedRefund`, we consider the order to be fully
    charged.
    If the sum of the transactionItem's charge amounts covers a part of the
    `order.total` - `order.totalGrantedRefund`, we treat the order as partially charged.

    NONE - the funds are not charged.
    PARTIAL - the funds that are charged don't cover the
    `order.total`-`order.totalGrantedRefund`
    FULL - the funds that are charged fully cover the
    `order.total`-`order.totalGrantedRefund`
    OVERCHARGED - the charged funds are bigger than the
    `order.total`-`order.totalGrantedRefund`
    """

    none = "none", _("The order is not charged.")
    partial = "partial", _("The order is partially charged")
    full = "full", _("The order is fully charged")
    overcharged = "overcharged", _("The order is overcharged")


class OrderGrantedRefundStatusChoices(TextChoices):
    """Represents the status of a granted refund.

    none - the refund on related transactionItem is not processed
    pending - the refund on related transactionItem is pending
    full - the refund on related transactionItem is fully processed
    fail - the refund on related transactionItem failed
    """

    none = "none", _("The refund on related transactionItem is not processed")
    pending = "pending", _("The refund on related transactionItem is pending")
    success = "success", _("The refund on related transactionItem is successfully processed")
    failure = "failure", _("The refund on related transactionItem failed")


class OrderOriginChoices(TextChoices):
    checkout = "checkout", _("Checkout")  # order created from checkout
    draft = "draft", _("Draft")  # order created from draft order
    reissue = "reissue", _("Reissue")  # order created from reissue existing one
    bulk_create = "bulk_create", _("Bulk create")  # order created from bulk upload

