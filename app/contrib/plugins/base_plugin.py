from dataclasses import dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
    Callable, Any
)
from copy import copy

from promise.promise import Promise
from app.core.enums import TextChoices
# from ..core.models import EventDelivery
# from ..graphql.core import ResolveInfo
from app.contrib.payment.interface import (
    #     CustomerSource,
    GatewayResponse,
    InitializedPaymentResponse,
    #     ListStoredPaymentMethodsRequestData,
    PaymentData,
    PaymentGateway,
    #     PaymentGatewayInitializeTokenizationRequestData,
    #     PaymentGatewayInitializeTokenizationResponseData,
    #     PaymentMethodData,
    #     PaymentMethodInitializeTokenizationRequestData,
    #     PaymentMethodProcessTokenizationRequestData,
    #     PaymentMethodTokenizationResponseData,
    #     StoredPaymentMethodRequestDeleteData,
    #     StoredPaymentMethodRequestDeleteResponseData,
    #     TransactionActionData,
    #     TransactionSessionResult,
)
# from ..thumbnail.models import Thumbnail

from .models import PluginConfiguration
from .repository import plugin_config_repo
from app.utils.prices import TaxedMoney

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.contrib.account.models import User, Address
    from app.contrib.order.models import (
        Order, OrderLine, Fulfillment, FulfillmentLine,
    )

    # from .schema import PluginConfigurationCreate
    # from ..app.models import App
    # from ..attribute.models import Attribute, AttributeValue
    # from ..channel.models import Channel
    # from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    # from ..checkout.models import Checkout
    # from ..core.middleware import Requestor

PluginConfigurationType = list[dict]


class ConfigurationTypeField(TextChoices):
    STRING = "string"
    MULTILINE = "multiline"
    BOOLEAN = "boolean"
    SECRET = "secret"
    SECRET_MULTILINE = "secret_multiline"
    PASSWORD = "password"
    OUTPUT = "output"
    # CHOICES = [
    #     (STRING, "Field is a String"),
    #     (MULTILINE, "Field is a Multiline"),
    #     (BOOLEAN, "Field is a Boolean"),
    #     (SECRET, "Field is a Secret"),
    #     (PASSWORD, "Field is a Password"),
    #     (SECRET_MULTILINE, "Field is a Secret multiline"),
    #     (OUTPUT, "Field is a read only"),
    # ]


@dataclass
class ExternalAccessTokens:
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    csrf_token: Optional[str] = None
    user: Optional["User"] = None


@dataclass
class ExcludedShippingMethod:
    id: str
    reason: Optional[str]


class BasePlugin:
    """Abstract class for storing all methods available for any plugin.

    All methods take previous_value parameter.
    previous_value contains a value calculated by the previous plugin in the queue.
    If the plugin is first, it will use default value calculated by the manager.
    """

    PLUGIN_NAME = ""
    PLUGIN_ID = ""
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None

    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = False
    HIDDEN = False

    @classmethod
    def check_plugin_id(cls, plugin_id: str) -> bool:
        """Check if given plugin_id matches with the PLUGIN_ID of this plugin."""
        return cls.PLUGIN_ID == plugin_id

    def __init__(
            self,
            *,
            configuration: PluginConfigurationType,
            is_active: bool,
            db_config: Optional["PluginConfiguration"] = None,
    ):
        self.configuration = self.get_plugin_configuration(configuration)
        self.is_active = is_active
        # self.requestor: Optional[RequestorOrLazyObject] = (
        #     SimpleLazyObject(requestor_getter) if requestor_getter else requestor_getter
        # )
        self.db_config = db_config

    def __del__(self) -> None:
        self.db_config = None
        self.configuration.clear()
        # self.requestor = None

    def __str__(self):
        return self.PLUGIN_NAME

    # Trigger when account is confirmed by user.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # is confirmed.
    account_confirmed: Callable[["User", None], None]

    # Trigger when account confirmation is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # confirmation is requested.
    account_confirmation_requested: Callable[
        ["User", str, str, Optional[str], None], None
    ]

    # Trigger when account change email is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # change email is requested.
    account_change_email_requested: Callable[["User", str, str, str, str, None], None]

    # Trigger when account set password is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # set password is requested.
    account_set_password_requested: Callable[["User", str, str, str, None], None]

    # Trigger when account delete is confirmed.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # delete is confirmed.
    account_deleted: Callable[["User", None], None]

    # Trigger when account email is changed.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # email is changed.
    account_email_changed: Callable[["User", None], None]

    # Trigger when account delete is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # delete is requested.
    account_delete_requested: Callable[["User", str, str, str, None], None]

    # Trigger when address is created.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # created.
    address_created: Callable[["Address", None], None]

    # Trigger when address is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # deleted.
    address_deleted: Callable[["Address", None], None]

    # Trigger when address is updated.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # updated.
    address_updated: Callable[["Address", None], None]

    authorize_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Calculate order line total.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a order line total. Return TaxedMoney.
    calculate_order_line_total: Callable[
        ["Order", "OrderLine", TaxedMoney], TaxedMoney
    ]

    # Calculate the shipping costs for the order.
    #
    # Update shipping costs in the order in case of changes in shipping address or
    # changes in draft order. Return TaxedMoney.
    calculate_order_shipping: Callable[["Order", TaxedMoney], TaxedMoney]

    # Calculate order total.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of an order total. Return TaxedMoney.
    calculate_order_total: Callable[
        ["Order", list["OrderLine"], TaxedMoney], TaxedMoney
    ]

    capture_payment: Callable[["PaymentData", Any], GatewayResponse]

    change_user_address: Callable[
        ["Address", Union[str, None], Union["User", None], bool, "Address"], "Address"
    ]

    confirm_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Trigger when user is created.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # created.
    customer_created: Callable[["User", Any], Any]

    # Trigger when user is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # deleted.
    customer_deleted: Callable[["User", Any, None], Any]

    # Trigger when user is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # updated.
    customer_updated: Callable[["User", Any, None], Any]

    # Trigger when user metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a user
    # metadata is updated.
    customer_metadata_updated: Callable[["User", Any, None], Any]

    # Trigger when fulfillment is created.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # created.
    fulfillment_created: Callable[["Fulfillment", bool, Any], Any]

    # Trigger when fulfillment is cancelled.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # cancelled.
    fulfillment_canceled: Callable[["Fulfillment", Any], Any]

    # Trigger when fulfillment is approved.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # approved.
    fulfillment_approved: Callable[["Fulfillment", Any], Any]

    # Trigger when fulfillment metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment
    # metadata is updated.
    fulfillment_metadata_updated: Callable[["Fulfillment", Any], Any]

    # get_taxes_for_order: Callable[["Order", str, Any], Optional["TaxData"]]

    get_client_token: Callable[[Any, Any], Any]

    # get_order_line_tax_rate: Callable[
    #     ["Order", "Product", "ProductVariant", Union["Address", None], Decimal],
    #     Decimal,
    # ]

    get_order_shipping_tax_rate: Callable[["Order", Any], Any]
    get_payment_config: Callable[[Any], Any]

    get_supported_currencies: Callable[[Any], Any]

    initialize_payment: Callable[
        [dict, Optional[InitializedPaymentResponse]], InitializedPaymentResponse
    ]

    # Trigger before invoice is deleted.
    #
    # Perform any extra logic before the invoice gets deleted.
    # Note there is no need to run invoice.delete() as it will happen in mutation.
    # invoice_delete: Callable[["Invoice", Any], Any]
    #
    # # Trigger when invoice creation starts.
    # # May return Invoice object.
    # # Overwrite to create invoice with proper data, call invoice.update_invoice.
    # invoice_request: Callable[
    #     ["Order", "Invoice", Union[str, None], Any], Optional["Invoice"]
    # ]
    #
    # # Trigger after invoice is sent.
    # invoice_sent: Callable[["Invoice", str, Any], Any]
    #
    # list_payment_sources: Callable[[str, Any], list["CustomerSource"]]
    #
    # list_stored_payment_methods: Callable[
    #     ["ListStoredPaymentMethodsRequestData", list["PaymentMethodData"]],
    #     list["PaymentMethodData"],
    # ]
    #
    # stored_payment_method_request_delete: Callable[
    #     [
    #         "StoredPaymentMethodRequestDeleteData",
    #         "StoredPaymentMethodRequestDeleteResponseData",
    #     ],
    #     "StoredPaymentMethodRequestDeleteResponseData",
    # ]
    #
    # payment_gateway_initialize_tokenization: Callable[
    #     [
    #         "PaymentGatewayInitializeTokenizationRequestData",
    #         "PaymentGatewayInitializeTokenizationResponseData",
    #     ],
    #     "PaymentGatewayInitializeTokenizationResponseData",
    # ]
    #
    # payment_method_initialize_tokenization: Callable[
    #     [
    #         "PaymentMethodInitializeTokenizationRequestData",
    #         "PaymentMethodTokenizationResponseData",
    #     ],
    #     "PaymentMethodTokenizationResponseData",
    # ]
    #
    # payment_method_process_tokenization: Callable[
    #     [
    #         "PaymentMethodProcessTokenizationRequestData",
    #         "PaymentMethodTokenizationResponseData",
    #     ],
    #     "PaymentMethodTokenizationResponseData",
    # ]
    #

    # Handle notification request.
    #
    # Overwrite this method if the plugin is responsible for sending notifications.
    # notify: Callable[["NotifyEventType", dict, Any], Any]

    # Trigger when order is cancelled.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # canceled.
    order_cancelled: Callable[["Order", Any, None], Any]

    # Trigger when order is expired.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # expired.
    order_expired: Callable[["Order", Any], Any]

    # Trigger when order is confirmed by staff.
    #
    # Overwrite this method if you need to trigger specific logic after an order is
    # confirmed.
    order_confirmed: Callable[["Order", Any], Any]

    # Trigger when order is created.
    #
    # Overwrite this method if you need to trigger specific logic after an order is
    # created.
    order_created: Callable[["Order", Any], Any]

    # Trigger when order is fulfilled.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fulfilled.
    order_fulfilled: Callable[["Order", Any], Any]

    # Trigger when order is fully paid.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fully paid.
    order_fully_paid: Callable[["Order", Any], Any]

    # Trigger when order is paid.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # received the payment.
    order_paid: Callable[["Order", Any], Any]

    # Trigger when order is refunded.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # refunded.
    order_refunded: Callable[["Order", Any], Any]

    # Trigger when order is fully refunded.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fully refunded.
    order_fully_refunded: Callable[["Order", Any], Any]

    # Trigger when order is updated.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # changed.
    order_updated: Callable[["Order", Any, None], Any]

    # Trigger when order metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when an order
    # metadata is changed.
    order_metadata_updated: Callable[["Order", Any], Any]

    # Trigger when orders are imported.
    #
    # Overwrite this method if you need to trigger specific logic when an order
    # is imported.
    order_bulk_created: Callable[[list["Order"], Any], Any]

    # # Trigger directly before order creation.
    # #
    # # Overwrite this method if you need to trigger specific logic before an order is
    # # created.
    # preprocess_order_creation: Callable[
    #     [
    #         "CheckoutInfo",
    #         Union[Iterable["CheckoutLineInfo"], None],
    #         Any,
    #     ],
    #     Any,
    # ]
    #
    process_payment: Callable[["PaymentData", Any], Any]

    transaction_charge_requested: Callable[["TransactionActionData", None], None]
    #
    # transaction_cancelation_requested: Callable[["TransactionActionData", None], None]
    #
    # transaction_refund_requested: Callable[["TransactionActionData", None], None]
    #
    # payment_gateway_initialize_session: Callable[
    #     [
    #         Decimal,
    #         Optional[list["PaymentGatewayData"]],
    #         Union["Checkout", "Order"],
    #         None,
    #     ],
    #     list["PaymentGatewayData"],
    # ]
    #
    # transaction_initialize_session: Callable[
    #     ["TransactionSessionData", None], "TransactionSessionResult"
    # ]
    #
    # transaction_process_session: Callable[
    #     ["TransactionSessionData", None], "TransactionSessionResult"
    # ]
    #
    # # Trigger when transaction item metadata is updated.
    # #
    # # Overwrite this method if you need to trigger specific logic when a transaction
    # # item metadata is updated.
    # transaction_item_metadata_updated: Callable[["TransactionItem", Any], Any]
    #

    refund_payment: Callable[["PaymentData", Any], GatewayResponse]

    # # Trigger when shipping price is created.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping
    # # price is created.
    # shipping_price_created: Callable[["ShippingMethod", None], None]
    #
    # # Trigger when shipping price is deleted.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping
    # # price is deleted.
    # shipping_price_deleted: Callable[["ShippingMethod", None, None], None]
    #
    # # Trigger when shipping price is updated.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping
    # # price is updated.
    # shipping_price_updated: Callable[["ShippingMethod", None], None]
    #
    # # Trigger when shipping zone is created.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping zone
    # # is created.
    # shipping_zone_created: Callable[["ShippingZone", None], None]
    #
    # # Trigger when shipping zone is deleted.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping zone
    # # is deleted.
    # shipping_zone_deleted: Callable[["ShippingZone", None, None], None]
    #
    # # Trigger when shipping zone is updated.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping zone
    # # is updated.
    # shipping_zone_updated: Callable[["ShippingZone", None], None]
    #
    # # Trigger when shipping zone metadata is updated.
    # #
    # # Overwrite this method if you need to trigger specific logic after a shipping zone
    # # metadata is updated.
    # shipping_zone_metadata_updated: Callable[["ShippingZone", None], None]
    #
    # Trigger when staff user is created.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # created.
    staff_created: Callable[["User", Any], Any]

    # Trigger when staff user is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # updated.
    staff_updated: Callable[["User", Any], Any]

    # Trigger when staff user is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # deleted.
    staff_deleted: Callable[["User", Any, None], Any]

    # Trigger when setting a password for staff is requested.
    #
    # Overwrite this method if you need to trigger specific logic after set
    # password for staff is requested.
    staff_set_password_requested: Callable[["User", str, str, str, None], None]

    void_payment: Callable[["PaymentData", Any], GatewayResponse]

    def get_payment_gateways(
            self,
            currency: Optional[str],
            previous_value,
    ) -> list["PaymentGateway"]:
        payment_config = (
            self.get_payment_config(previous_value)
            if hasattr(self, "get_payment_config")
            else []
        )
        currencies = (
            self.get_supported_currencies([])
            if hasattr(self, "get_supported_currencies")
            else []
        )
        if currency and currency not in currencies:
            return []
        gateway = PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=payment_config,
            currencies=currencies,
        )
        return [gateway]

    @classmethod
    def _update_config_items(
            cls, configuration_to_update: list[dict], current_config: list[dict]
    ):
        config_structure: dict = (
            cls.CONFIG_STRUCTURE if cls.CONFIG_STRUCTURE is not None else {}
        )
        configuration_to_update_dict = {
            c_field["name"]: c_field.get("value") for c_field in configuration_to_update
        }
        for config_item in current_config:
            new_value = configuration_to_update_dict.get(config_item["name"])
            if new_value is None:
                continue
            item_type = config_structure.get(config_item["name"], {}).get("type")
            new_value = cls._clean_configuration_value(item_type, new_value)
            if new_value is not None:
                config_item.update([("value", new_value)])

        # Get new keys that don't exist in current_config and extend it.
        current_config_keys = set(c_field["name"] for c_field in current_config)
        missing_keys = set(configuration_to_update_dict.keys()) - current_config_keys
        for missing_key in missing_keys:
            if not config_structure.get(missing_key):
                continue
            item_type = config_structure.get(missing_key, {}).get("type")
            new_value = cls._clean_configuration_value(
                item_type, configuration_to_update_dict[missing_key]
            )
            if new_value is None:
                continue
            current_config.append(
                {
                    "name": missing_key,
                    "value": new_value,
                }
            )

    @classmethod
    def _clean_configuration_value(cls, item_type, new_value):
        """Clean the value that is saved in plugin configuration.

        Change the string provided as boolean into the bool value.
        Return None for Output type, as it's read only field.
        """
        if (
                item_type == ConfigurationTypeField.BOOLEAN
                and new_value
                and not isinstance(new_value, bool)
        ):
            new_value = new_value.lower() == "true"
        if item_type == ConfigurationTypeField.OUTPUT:
            # OUTPUT field is read only. No need to update it
            return
        return new_value

    @classmethod
    def validate_plugin_configuration(
            cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct.

        Raise django.core.exceptions.ValidationError otherwise.
        """
        return

    @classmethod
    def pre_save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Trigger before plugin configuration will be saved.

        Overwrite this method if you need to trigger specific logic before saving a
        plugin configuration.
        """

    @classmethod
    async def save_plugin_configuration(
            cls,
            plugin_configuration: "PluginConfiguration",
            cleaned_data: dict,
            async_db: "AsyncSession",
    ):
        current_config = plugin_configuration.configuration
        configuration_to_update = cleaned_data.get("configuration")
        obj_in = {}
        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)

        if "is_active" in cleaned_data:
            obj_in["is_active"] = cleaned_data["is_active"]

        cls.validate_plugin_configuration(plugin_configuration)
        cls.pre_save_plugin_configuration(plugin_configuration)

        if obj_in:
            await plugin_config_repo.update(
                async_db=async_db,
                db_obj=plugin_configuration,
                obj_in={}
            )

        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)

        return plugin_configuration

    @classmethod
    def _append_config_structure(cls, configuration: PluginConfigurationType):
        """Append configuration structure to config from the database.

        Database stores "key: value" pairs, the definition of fields should be declared
        inside of the plugin. Based on this, the plugin will generate a structure of
        configuration with current values and provide access to it via API.
        """
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        fields_without_structure = []
        for configuration_field in configuration:
            structure_to_add = config_structure.get(configuration_field.get("name"))
            if structure_to_add:
                configuration_field.update(structure_to_add)
            else:
                fields_without_structure.append(configuration_field)

        if fields_without_structure:
            [
                configuration.remove(field)  # type: ignore
                for field in fields_without_structure
            ]

    @classmethod
    def _update_configuration_structure(cls, configuration: PluginConfigurationType):
        updated_configuration = []
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        desired_config_keys = set(config_structure.keys())
        for config_field in configuration:
            if config_field["name"] not in desired_config_keys:
                continue
            updated_configuration.append(copy(config_field))

        configured_keys = set(d["name"] for d in updated_configuration)
        missing_keys = desired_config_keys - configured_keys

        if not missing_keys:
            return updated_configuration

        default_config = cls.DEFAULT_CONFIGURATION
        if not default_config:
            return updated_configuration

        update_values = [copy(k) for k in default_config if k["name"] in missing_keys]
        if update_values:
            updated_configuration.extend(update_values)

        return updated_configuration

    @classmethod
    def get_default_active(cls):
        return cls.DEFAULT_ACTIVE

    def get_plugin_configuration(
            self, configuration: PluginConfigurationType
    ) -> PluginConfigurationType:
        if not configuration:
            configuration = []
        configuration = self._update_configuration_structure(configuration)
        if configuration:
            # Let's add a translated descriptions and labels
            self._append_config_structure(configuration)
        return configuration

    def resolve_plugin_configuration(
            self, request
    ) -> Union[PluginConfigurationType, Promise[PluginConfigurationType]]:
        # Override this function to customize resolving plugin configuration in API.
        return self.configuration

    def is_event_active(self, event: str, channel=Optional[str]):
        return hasattr(self, event)
