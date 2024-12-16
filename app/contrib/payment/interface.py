from abc import ABC, abstractmethod

from uuid import UUID
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from app.contrib.payment import StorePaymentMethodChoices

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]

if TYPE_CHECKING:
    from decimal import Decimal
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.contrib.payment import TransactionKindChoices


@dataclass
class PaymentMethodInfo:
    """Uniform way to represent payment method information."""
    first_4: Optional[str] = None
    last_4: Optional[str] = None
    exp_year: Optional[int] = None
    exp_month: Optional[int] = None
    brand: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    payment_order_id: Optional[str] = None  # Order unique id in payment server


@dataclass
class GatewayResponse:
    """Dataclass for storing gateway response.

    Used for unifying the representation of gateway response.
    It is required to communicate between Saleor and given payment gateway.
    """

    is_success: bool
    action_required: bool
    kind: "TransactionKindChoices"  # use "TransactionKindChoices" class
    amount: "Decimal"
    currency: str
    transaction_id: str
    error: Optional[str] = None
    customer_id: Optional[str] = None
    payment_method_info: Optional["PaymentMethodInfo"] = None
    raw_response: Optional[Dict[str, str]] = None
    action_required_data: Optional[JSONType] = None
    # Some gateway can process transaction asynchronously. This value define if we
    # should create new transaction based on this response
    transaction_already_processed: bool = False
    psp_reference: Optional[str] = None
    private_meta_data: Optional[Dict[str, str]] = None


@dataclass
class PaymentData:
    """Dataclass for storing all payment information.

    Used for unifying the representation of data.
    It is required to communicate between Saleor and given payment gateway.
    """
    gateway: str
    amount: "Decimal"
    currency: str
    payment_id: UUID
    customer_email: str
    customer_ip_address: Optional[str] = None
    token: Optional[str] = None
    customer_id: Optional[str] = None  # stores payment gateway customer ID
    data: Optional[dict] = None
    store_payment_method: Optional[StorePaymentMethodChoices] = StorePaymentMethodChoices.NONE
    payment_metadata: Dict[str, str] = field(default_factory=dict)
    psp_reference: Optional[str] = None


@dataclass
class TokenConfig:
    """Dataclass for payment gateway token fetching customization."""
    customer_id: Optional[str] = None


@dataclass
class GatewayConfig:
    """Dataclass for storing gateway config data.

    Used for unifying the representation of config data.
    It is required to communicate between Saleor and given payment gateway.
    """

    gateway_name: str
    auto_capture: bool
    supported_currencies: str
    # Each gateway has different connection data so we are not able to create
    # a unified structure
    connection_params: dict[str, Any]
    store_customer: bool = False
    require_3d_secure: bool = False


@dataclass
class CustomerSource:
    """Dataclass for storing information about stored payment sources in gateways."""

    id: str
    gateway: str
    credit_card_info: Optional[PaymentMethodInfo] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class PaymentGateway:
    """Dataclass for storing information about a payment gateway."""

    id: str
    name: str
    currencies: List[str]
    config: List[Dict[str, Any]]


@dataclass
class InitializedPaymentResponse:
    gateway: str
    name: str
    data: Optional[JSONType] = None


class PaymentInterface(ABC):
    @abstractmethod
    def list_payment_gateways(
            self,
            async_db: "AsyncSession",
            currency: Optional[str] = None,
            active_only: bool = True,
    ) -> list["PaymentGateway"]:
        pass

    @abstractmethod
    def authorize_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def capture_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    async def refund_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    async def void_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    async def confirm_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession",
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    async def token_is_required_as_payment_input(
            self, gateway: str, async_db: "AsyncSession"
    ) -> bool:
        pass

    @abstractmethod
    async def process_payment(
            self, gateway: str, payment_information: "PaymentData", async_db: "AsyncSession"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    async def get_client_token(
            self, async_db: "AsyncSession", gateway: str, token_config: "TokenConfig"
    ) -> str:
        pass

    @abstractmethod
    def list_payment_sources(
            self, async_db: "AsyncSession", gateway: str, customer_id: str
    ) -> list["CustomerSource"]:
        pass
