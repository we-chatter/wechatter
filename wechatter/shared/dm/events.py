# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   events.py
 
@Time    :   2021/4/1 5:05 下午
 
@Desc    :   Event就是对bot一切行为的抽象，每一个具体的事件类都继承自Event基类
 
"""

import abc
import json
import logging
import re
from abc import ABC

import jsonpickle
import time
import uuid
from dateutil import parser
from datetime import datetime
from typing import (
    List,
    Dict,
    Text,
    Any,
    Type,
    Optional,
    TYPE_CHECKING,
    Iterable,
    cast,
    Tuple,
)

logger = logging.getLogger(__name__)


def deserialise_events(serialized_events: List[Dict[Text, Any]]) -> List["Event"]:
    """Convert a list of dictionaries to a list of corresponding events.

    Example format:
        [{"event": "slot", "value": 5, "name": "my_slot"}]
    """

    deserialised = []

    for e in serialized_events:
        if "event" in e:
            event = Event.from_parameters(e)
            if event:
                deserialised.append(event)
            else:
                logger.warning(
                    f"Unable to parse event '{event}' while deserialising. The event"
                    " will be ignored."
                )

    return deserialised