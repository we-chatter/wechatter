# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   __init__.py.py
 
@Time    :   2020/11/10 9:04 上午
 
@Desc    :
 
"""
from config.config import Config


def load_config():
    """
    Load a config class
    """

    return Config


CONFIG = load_config()