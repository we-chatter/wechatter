# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   trackers.py
 
@Time    :   2021/4/1 5:05 下午
 
@Desc    :
 
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

