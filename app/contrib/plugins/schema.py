from typing import Optional, List, Union
from decimal import Decimal

from pydantic import Field

from app.core.schema import BaseModel, VisibleBase, ChoiceBase
from app.contrib.plugins.base_plugin import ConfigurationTypeField


class ConfigurationItemInput(BaseModel):
    name: str = Field(description="Name of the field to update.")
    value: str = Field(description="Value of the given field to update.")


class PluginConfigurationBase(BaseModel):
    is_active: bool = Field(..., alias="isActive")
    configuration: List[ConfigurationItemInput]


class ConfigurationItem(VisibleBase):
    name: str = Field(description="Name of the field.")
    value: Optional[Union[str, bool, int, float, Decimal]] = Field(None, description="Current value of the field.")
    type: ConfigurationTypeField = Field(description="Type of the field.")
    help_text: Optional[str] = Field(None, description="Help text for the field.", alias="helpText")
    label: Optional[str] = Field(None, description="Label for the field.")

    class Meta:
        description = "Stores information about a single configuration field."


class PluginVisible(VisibleBase):
    id: str
    name: str
    description: str
    is_active: bool = Field(alias="isActive")
    configuration: List[ConfigurationItem]
