# -*- coding: utf-8 -*-

"""
@Author  :   Xu

@Software:   PyCharm

@File    :   run_server.py

@Time    :   2020/8/26 2:50 下午

@Desc    :

"""
import asyncio
import concurrent.futures
import logging
import multiprocessing
import os
import tempfile
import traceback
from collections import defaultdict
from functools import reduce, wraps
from inspect import isawaitable
from pathlib import Path
from http import HTTPStatus

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
from pathlib import Path

# parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, parentdir)

from wechatter.config import CONFIG

import aiohttp
from sanic import Sanic, response
from sanic.response import text, HTTPResponse
from sanic.request import Request
from sanic_cors import CORS

import wechatter
import wechatter.utils
import wechatter.shared
import wechatter.utils.endpoints
import wechatter.shared.utils
import wechatter.shared.utils.io
from wechatter.model_training import train_async

from wechatter.shared.dialogue_config import (
    DOCS_URL_TRAINING_DATA,
    DEFAULT_MODELS_PATH,
    DEFAULT_DOMAIN_PATH
)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

app = Sanic(__name__)

logging.info('wechatter loading...')


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
    return text('Welcome to wechatty dialogue engine，Current version is:' + wechatter.__version__)


@app.get('/version')
async def version(request: Request):
    """
    Get version information
    :param request:
    :return:
    """
    return response.text(
        "Hello from Wechatter:" + wechatter.__version__
    )


@app.post("/model/train")
async def train(request: Request) -> HTTPResponse:
    """
    训练模型
    方式一：加载数据库，写入临时文件，训练模型
    :param temporary_directory:
    :param request:
    :return:
    """
    training_payload = _training_payload_from_json(request)

    try:
        # a = 111
        # with app.active_training_processes.get_lock():
        #     app.active_training_processes.value += 1
        training_result = await train_async(**training_payload)

        if training_result.model:
            filename = os.path.basename(training_result.model)

            return await response.file(
                training_result.model,
                filename=filename,

            )
        else:
            raise ErrorResponse(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "TrainingError",
                "Ran training, but it finished without a trained model.",
            )
    except ErrorResponse as e:
        raise e


def _training_payload_from_json(request: Request) -> Dict[Text, Any]:
    """
    读取请求的json文件，同时写入一个临时文件夹
    :param request:
    :param temp_dir:
    :return:
    """
    logging.debug(
        "Extracting JSON payload with Markdown training data from request body."
    )

    request_payload = request.json
    _validate_json_training_payload(request_payload)

    temp_dir= ''
    config_path = os.path.join(temp_dir, "config.yml")

    wechatter.shared.utils.io.write_text_file(request_payload["config"], config_path)

    if "nlu" in request_payload:
        nlu_path = os.path.join(temp_dir, "nlu.md")
        wechatter.shared.utils.io.write_text_file(request_payload["nlu"], nlu_path)

    if "stories" in request_payload:
        stories_path = os.path.join(temp_dir, "stories.md")
        wechatter.shared.utils.io.write_text_file(request_payload["stories"], stories_path)

    if "responses" in request_payload:
        responses_path = os.path.join(temp_dir, "responses.md")
        wechatter.shared.utils.io.write_text_file(
            request_payload["responses"], responses_path
        )

    domain_path = DEFAULT_DOMAIN_PATH
    if "domain" in request_payload:
        domain_path = os.path.join(temp_dir, "domain.yml")
        wechatter.shared.utils.io.write_text_file(request_payload["domain"], domain_path)

    model_output_directory = str(temp_dir)
    if request_payload.get(
            "save_to_default_model_directory",
            wechatter.utils.endpoints.bool_arg(request, "save_to_default_model_directory", True),
    ):
        model_output_directory = DEFAULT_MODELS_PATH

    return dict(
        domain=domain_path,
        config=config_path,
        training_files=str(temp_dir),
        output=model_output_directory,
        force_training=request_payload.get(
            "force", wechatter.utils.endpoints.bool_arg(request, "force_training", False)
        ),
        dm_additional_arguments=_extract_dm_additional_arguments(request),
        nlu_additional_arguments=_extract_nlu_additional_arguments(request),
    )


def _validate_json_training_payload(rjs: Dict):
    if "config" not in rjs:
        raise ErrorResponse(
            HTTPStatus.BAD_REQUEST,
            "BadRequest",
            "The training request is missing the required key `config`.",
            {"parameter": "config", "in": "body"},
        )

    if "nlu" not in rjs and "stories" not in rjs:
        raise ErrorResponse(
            HTTPStatus.BAD_REQUEST,
            "BadRequest",
            "To train a Rasa model you need to specify at least one type of "
            "training data. Add `nlu` and/or `stories` to the request.",
            {"parameters": ["nlu", "stories"], "in": "body"},
        )

    if "stories" in rjs and "domain" not in rjs:
        raise ErrorResponse(
            HTTPStatus.BAD_REQUEST,
            "BadRequest",
            "To train a Rasa model with story training data, you also need to "
            "specify the `domain`.",
            {"parameter": "domain", "in": "body"},
        )

    if "force" in rjs or "save_to_default_model_directory" in rjs:
        wechatter.shared.utils.io.raise_deprecation_warning(
            "Specifying 'force' and 'save_to_default_model_directory' as part of the "
            "JSON payload is deprecated. Please use the header arguments "
            "'force_training' and 'save_to_default_model_directory'.",
            docs=_docs("/api/http-api"),
        )


class ErrorResponse(Exception):
    """Common exception to handle failing API requests."""

    def __init__(
        self,
        status: Union[int, HTTPStatus],
        reason: Text,
        message: Text,
        details: Any = None,
        help_url: Optional[Text] = None,
    ) -> None:
        """Creates error.

        Args:
            status: The HTTP status code to return.
            reason: Short summary of the error.
            message: Detailed explanation of the error.
            details: Additional details which describe the error. Must be serializable.
            help_url: URL where users can get further help (e.g. docs).
        """
        self.error_info = {
            "version": wechatter.__version__,
            "status": "failure",
            "message": message,
            "reason": reason,
            "details": details or {},
            "help": help_url,
            "code": status,
        }
        self.status = status
        logging.error(message)
        super(ErrorResponse, self).__init__()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9015, auto_reload=True, workers=4)
