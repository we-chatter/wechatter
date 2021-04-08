# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   trackers.py
 
@Time    :   2021/4/1 5:05 下午
 
@Desc    :   对话状态跟踪
 
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

import wechatter.shared.utils.common
from typing import Union
from enum import Enum

from wechatter.shared.dialogue_config import DOCS_URL_TRAINING_DATA
from wechatter.shared.dm.dm_config import (
    LOOP_NAME,
    EXTERNAL_MESSAGE_PREFIX,
    ACTION_NAME_SENDER_ID_CONNECTOR_STR,
    IS_EXTERNAL,
    USE_TEXT_FOR_FEATURIZATION,
    LOOP_INTERRUPTED,
    ENTITY_LABEL_SEPARATOR,
    ACTION_SESSION_START_NAME,
    ACTION_LISTEN_NAME,
)
from wechatter.shared.dm.slots import Slot
from wechatter.shared.exceptions import UnsupportedFeatureException
from wechatter.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_TYPE,
    INTENT,
    TEXT,
    ENTITIES,
    ENTITY_ATTRIBUTE_VALUE,
    ACTION_TEXT,
    ACTION_NAME,
    INTENT_NAME_KEY,
    ENTITY_ATTRIBUTE_ROLE,
    ENTITY_ATTRIBUTE_GROUP,
)

logger = logging.getLogger(__name__)


class EventVerbosity(Enum):
    """Filter on which events to include in tracker dumps."""

    # no events will be included
    NONE = 1

    # all events, that contribute to the trackers state are included
    # these are all you need to reconstruct the tracker state
    APPLIED = 2

    # include even more events, in this case everything that comes
    # after the most recent restart event. this will also include
    # utterances that got reverted and actions that got undone.
    AFTER_RESTART = 3

    # include every logged event
    ALL = 4


class AnySlotDict(dict):
    """A slot dictionary that pretends every slot exists, by creating slots on demand.

    This only uses the generic slot type! This means certain functionality wont work,
    e.g. properly featurizing the slot."""

    def __missing__(self, key) -> Slot:
        value = self[key] = Slot(key)
        return value

    def __contains__(self, key) -> bool:
        return True


class DialogueStateTracker:
    """
    dst实现
    """

