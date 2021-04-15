# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   model.py
 
@Time    :   2021/4/14 6:26 下午
 
@Desc    :   模型构建
 
"""

import copy
import glob
import hashlib
import logging
import os
import shutil
from subprocess import CalledProcessError, DEVNULL, check_output  # skipcq:BAN-B404
import tempfile
import typing
from pathlib import Path
from typing import Any, Text, Tuple, Union, Optional, List, Dict, NamedTuple

import wechatter.shared.utils.io
import wechatter.utils.io

from wechatter.shared.dialogue_config import (
    CONFIG_KEYS_CORE,
    CONFIG_KEYS_NLU,
    CONFIG_KEYS,
    DEFAULT_MODELS_PATH,
    DEFAULT_DOMAIN_PATH,
    DEFAULT_CORE_SUBDIRECTORY_NAME,
    DEFAULT_NLU_SUBDIRECTORY_NAME
)

from wechatter.exceptions import ModelNotFound

logger = logging.getLogger(__name__)


