# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   interpreter.py
 
@Time    :   2021/4/6 2:14 下午
 
@Desc    :   对话管理解释器
 
"""
import aiohttp

import logging

import os
from typing import Text, Dict, Any, Union, Optional

from wechatter.dm import dm_config
from wechatter.utils.endpoints import EndpointConfig


logger = logging.getLogger(__name__)


class WechatterNLUHttpInterpreter():

    def __init__(self, endpoint_config: Optional[EndpointConfig] = None) -> None:
        if endpoint_config:
            self.endpoint_config = endpoint_config
        else:
            self.endpoint_config = EndpointConfig(dm_config.DEFAULT_SERVER_URL)
