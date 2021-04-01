# -*- coding: utf-8 -*-

"""
@Author  :   Xu

@Software:   PyCharm

@File    :   run_server.py

@Time    :   2020/8/26 2:50 下午

@Desc    :

"""
import datetime
import json
import os
import sys
import logging

from typing import (
    Any,
    Callable,
    List,
    Optional,
    Text,
    Union,
    Dict,
    TYPE_CHECKING,
    NoReturn
)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from wechatter.config import CONFIG

from sanic import Sanic, response
from sanic.response import text, HTTPResponse
from sanic.request import Request
from sanic_cors import CORS

import wechatter

logger = logging.getLogger(__name__)

app = Sanic(__name__)


def configure_cors(
        app: Sanic, cors_origins: Union[Text, List[Text], None] = ""
) -> None:
    """Configure CORS origins for the given app."""

    # Workaround so that socketio works with requests from other origins.
    # https://github.com/miguelgrinberg/python-socketio/issues/205#issuecomment-493769183
    app.config.CORS_AUTOMATIC_OPTIONS = True
    app.config.CORS_SUPPORTS_CREDENTIALS = True
    app.config.CORS_EXPOSE_HEADERS = "filename"

    CORS(
        app, resources={r"/*": {"origins": cors_origins or ""}}, automatic_options=True
    )


# def create_app(
#         cors_origins: Union[Text, List[Text], None] = "*",
# ):
#     app = Sanic(__name__)
app.update_config(CONFIG)  # 系统配置信息
# configure_cors(app, cors_origins)  # 解决跨域问题


@app.route("/")
async def test(request):
    return text('Welcome to wechatty dialogue engine')


@app.get('/version')
async def version(request: Request):
    """
    Get version information
    :param request:
    :return:
    """
    return response.json(
        {
            "version": wechatter.__version__,
        }
    )


async def train(request: Request) -> HTTPResponse:
    """
    训练模型
    :param request:
    :return:
    """
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9015, auto_reload=True)