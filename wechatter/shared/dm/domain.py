# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   domain.py
 
@Time    :   2021/4/1 5:04 下午
 
@Desc    :   domain实现
 
"""

import copy
import collections
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    NamedTuple,
    NoReturn,
    Optional,
    Set,
    Text,
    Tuple,
    Union,
    TYPE_CHECKING,
    Iterable,
)

from wechatter.shared.exceptions import WechatterException

logger = logging.getLogger(__name__)


class InvalidDomain(WechatterException):
    """
    Exception that can be raised when domain is not valid.
    """

class ActionNotFoundException(ValueError, WechatterException):
    """
    Raised when an action name could not be found.
    """

class Domain:
    """

    """



