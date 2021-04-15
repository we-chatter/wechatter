# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   slots.py
 
@Time    :   2021/4/1 5:05 下午
 
@Desc    :   槽位的处理逻辑
 
"""

import logging

from typing import Any, Dict, List, Optional, Text, Type

import wechatter.shared.dm.dm_config
from wechatter.shared.exceptions import WechatterException
import wechatter.shared.utils.common
import wechatter.shared.utils.io
from wechatter.shared.dialogue_config import DOCS_URL_SLOTS

logger = logging.getLogger(__name__)


class InvalidSlotTypeException(WechatterException):
    """Raised if a slot type is invalid."""


class InvalidSlotConfigError(WechatterException, ValueError):
    """Raised if a slot's config is invalid."""


class Slot:
    """
    Key-value store for storing information during a conversation.
    """

    type_name = None

    def __init__(
            self,
            name: Text,
            initial_value: Any = None,
            value_reset_delay: Optional[int] = None,
            auto_fill: bool = True,
            influence_conversation: bool = True,
    ) -> None:
        """Create a Slot.

        Args:
            name: The name of the slot.
            initial_value: The initial value of the slot.
            value_reset_delay: After how many turns the slot should be reset to the
                initial_value. This is behavior is currently not implemented.
            auto_fill: `True` if the slot should be filled automatically by entities
                with the same name.
            influence_conversation: If `True` the slot will be featurized and hence
                influence the predictions of the dialogue polices.
        """
        self.name = name
        self._value = initial_value
        self.initial_value = initial_value
        self._value_reset_delay = value_reset_delay
        self.auto_fill = auto_fill
        self.influence_conversation = influence_conversation
        self._has_been_set = False

    def feature_dimensionality(self) -> int:
        """How many features this single slot creates.

        Returns:
            The number of features. `0` if the slot is unfeaturized. The dimensionality
            of the array returned by `as_feature` needs to correspond to this value.
        """
        if not self.influence_conversation:
            return 0

        return self._feature_dimensionality()

    def _feature_dimensionality(self) -> int:
        """See the docstring for `feature_dimensionality`."""
        return 1

    def has_features(self) -> bool:
        """Indicate if the slot creates any features."""
        return self.feature_dimensionality() != 0

    def value_reset_delay(self) -> Optional[int]:
        """After how many turns the slot should be reset to the initial_value.

        If the delay is set to `None`, the slot will keep its value forever."""
        # TODO: FUTURE this needs to be implemented - slots are not reset yet
        return self._value_reset_delay

    def as_feature(self) -> List[float]:
        if not self.influence_conversation:
            return []

        return self._as_feature()

    def _as_feature(self) -> List[float]:
        raise NotImplementedError(
            "Each slot type needs to specify how its "
            "value can be converted to a feature. Slot "
            "'{}' is a generic slot that can not be used "
            "for predictions. Make sure you add this "
            "slot to your domain definition, specifying "
            "the type of the slot. If you implemented "
            "a custom slot type class, make sure to "
            "implement `.as_feature()`."
            "".format(self.name)
        )

    def reset(self) -> None:
        """Resets the slot's value to the initial value."""
        self.value = self.initial_value
        self._has_been_set = False

    @property
    def value(self) -> Any:
        """Gets the slot's value."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Sets the slot's value."""
        self._value = value
        self._has_been_set = True

    @property
    def has_been_set(self) -> bool:
        """Indicates if the slot's value has been set."""
        return self._has_been_set

    def __str__(self) -> Text:
        return f"{self.__class__.__name__}({self.name}: {self.value})"

    def __repr__(self) -> Text:
        return f"<{self.__class__.__name__}({self.name}: {self.value})>"

    @staticmethod
    def resolve_by_type(type_name) -> Type["Slot"]:
        """Returns a slots class by its type name."""
        for cls in wechatter.shared.utils.common.all_subclasses(Slot):
            if cls.type_name == type_name:
                return cls
        try:
            return wechatter.shared.utils.common.class_from_module_path(type_name)
        except (ImportError, AttributeError):
            raise InvalidSlotTypeException(
                f"Failed to find slot type, '{type_name}' is neither a known type nor "
                f"user-defined. If you are creating your own slot type, make "
                f"sure its module path is correct. "
                f"You can find all build in types at {DOCS_URL_SLOTS}"
            )

    def persistence_info(self) -> Dict[str, Any]:
        return {
            "type": wechatter.shared.utils.common.module_path_from_instance(self),
            "initial_value": self.initial_value,
            "auto_fill": self.auto_fill,
            "influence_conversation": self.influence_conversation,
        }


class FloatSlot:
    """
    数字类型slot
    """
    type_name = "float"

    def __init__(
            self,
            name: Text,
            initial_value: Optional[float] = None,
            value_reset_delay: Optional[int] = None,
            auto_fill: bool = True,
            max_value: float = 1.0,
            min_value: float = 0.0,
            influence_conversation: bool = True,
    ) -> None:
        super().__init__(
            name,
            initial_value,
            value_reset_delay,
            auto_fill,
            influence_conversation
        )
        self.max_value = max_value
        self.min_value = min_value

        if min_value >= max_value:
            raise InvalidSlotConfigError(
                "Float slot ('{}') created with an invalid range "
                "using min ({}) and max ({}) values. Make sure "
                "min is smaller than max."
                "".format(self.name, self.min_value, self.max_value)
            )

        if initial_value is not None and not (min_value <= initial_value <= max_value):
            wechatter.shared.utils.io.raise_warning(
                f"Float slot ('{self.name}') created with an initial value "
                f"{self.value}. This value is outside of the configured min "
                f"({self.min_value}) and max ({self.max_value}) values."
            )

    def _as_feature(self) -> List[float]:
        try:
            capped_value = max(self.min_value, min(self.max_value, float(self.value)))
            if abs(self.max_value - self.min_value) > 0:
                covered_range = abs(self.max_value - self.min_value)
            else:
                covered_range = 1
            return [1.0, (capped_value - self.min_value) / covered_range]
        except (TypeError, ValueError):
            return [0.0, 0.0]

    def persistence_info(self) -> Dict[Text, Any]:
        """Returns relevant information to persist this slot."""
        d = super().persistence_info()
        d["max_value"] = self.max_value
        d["min_value"] = self.min_value
        return d

    def _feature_dimensionality(self) -> int:
        return len(self.as_feature())


class BooleanSlot(Slot):
    type_name = "bool"

    def _as_feature(self) -> List[float]:
        try:
            if self.value is not None:
                return [1.0, float(bool_from_any(self.value))]
            else:
                return [0.0, 0.0]
        except (TypeError, ValueError):
            # we couldn't convert the value to float - using default value
            return [0.0, 0.0]

    def _feature_dimensionality(self) -> int:
        return len(self.as_feature())


class AnySlot:
    """

    """
    pass


class TextSlot(Slot):
    """

    """
    type_name = "text"

    def _as_feature(self) -> List[float]:
        return [1.0 if self.value is not None else 0.0]


class ListSlot(Slot):
    """

    """
    type_name = "list"

    def _as_feature(self) -> List[float]:
        try:
            if self.value is not None and len(self.value) > 0:
                return [1.0]
            else:
                return [0.0]
        except (TypeError, ValueError):
            # we couldn't convert the value to a list - using default value
            return [0.0]


class CategoricalSlot:
    """

    """


def bool_from_any(x: Any) -> bool:
    """ Converts bool/float/int/str to bool or raises error """

    if isinstance(x, bool):
        return x
    elif isinstance(x, (float, int)):
        return x == 1.0
    elif isinstance(x, str):
        if x.isnumeric():
            return float(x) == 1.0
        elif x.strip().lower() == "true":
            return True
        elif x.strip().lower() == "false":
            return False
        else:
            raise ValueError("Cannot convert string to bool")
    else:
        raise TypeError("Cannot convert to bool")
